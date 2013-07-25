r.ui.Suggest = Backbone.View.extend({
    requestThrottleTimeout: 333,

    events: {
        'keydown input': 'keyDown',
         'keyup input': 'keyUp',
         'input input': 'inputEvent',
         'click input': 'queryChanged',
         'blur input': 'defocused',
         'mouseout .suggestbox li': 'itemHoverOut',
         'mouseover .suggestbox li': 'itemHover',
         'mousedown .suggestbox li': 'itemMouseDown',
         'click .suggestbox li': 'itemClick',
         'focus input': 'show'
    },

    initialize: function() {
        this.$el.addClass('suggestarea')
        this.$input = this.$el.find('input').first()
            .addClass('suggestquery')
            .attr('autocomplete', 'off')
        this.cache = new r.utils.LRUCache()
        this.selection = -1
        this.query = _.throttle(this._query, this.requestThrottleTimeout)
    },

    defocused: function() {
        if (!this.$el.children(':focus').size()) {
            this.hide()
            this.stop()
        }
    },

    inputEvent: function() {
        this.ready = true
        this.queryChanged()
    },

    setText: function(val) {
        this.$input.val(val)
    },

    val: function() {
        return this.$input.val()
    },

    visible: function() {
        if (!this.$suggestBox) {
            return false
        }
        return this.$suggestBox.is(':visible')
    },

    size: function() {
        return this.$suggestBox.children('li').size()
    },

    deselectAll: function() {
        this.$suggestBox.children('li.selected').removeClass('selected')
    },

    itemMouseDown: function(e) {
        e.preventDefault()
    },

    itemClick: function(e) {
        e.preventDefault()
        this.setText(this.views[this.selection].text())
        this.stop()
        this.hide()
    },

    stop: function() {
        if (this.req) {
            this.req.abort()
        }
        this.loading(false)
    },

    itemHoverOut: function() {
        if (!this.$input.is(':focus')) {
            this.$input.focus()
        }
    },

    itemHover: function(e) {
        this.deselectAll()
        var $item = $(e.currentTarget)
        this.selection = $item.index()
        this.views[this.selection].selected()
    },

    changeSelectionBy: function(difference) {
        this.deselectAll()
        this.selection += difference
        var size = this.size()
        if (this.selection >= size) {
            this.selection = -1
        } else if (this.selection < -1) {
            this.selection = size - 1
        }
        if (this.selection == -1) {
            this.setText(this.lastQuery)
        } else {
            this.setText(this.views[this.selection].selected().text())
        }
    },

    keyUp: function(e) {
        if (e.keyCode == 13) {
            if (this.selection >= 0) {
                e.preventDefault()
                this.views[this.selection].clicked()
                this.stop()
                this.hide()
            }
        } else if (e.keyCode == 37 || e.keyCode == 39) {
            this.queryChanged()
        } else if (e.keyCode == 8) {
            this.queryChanged()
        }
    },

    keyDown: function(e) {
        if (!this.visible()) {
            return
        }
        if (e.keyCode == 38 || e.keyCode == 40) {
            e.preventDefault()
            this.changeSelectionBy(e.keyCode == 38 ? -1 : 1)
        } else if (e.keyCode == 13) {
            if (this.selection >= 0) {
                e.preventDefault()
            }
        }
    },

    queryChanged: function() {
        var query = this.val()
        if (!query) {
            this.stop()
            this.hide()
        }
        if (query != this.lastQuery) {
            this.query(query)
        }
    },

    show: function() {
        this.query(this.val())
    },

    hide: function() {
        if (this.$suggestBox) {
            this.$suggestBox.hide()
        }
    },

    queryParams: function(query) {
        return {query: query}
    },

    loading: function(done) {
        if (!_.isUndefined(done)) {
            this.$el.toggleClass('working', done)
            return this
        } else {
            return this.$el.hasClass('working')
        }
    },

    _query: function(query) {
        if (!this.ready) {
            return
        }
        this.lastQuery = query
        if (this.loading()) {
            this.dirty = true
            return
        }
        this.dirty = false
        if (!query) {
            this.hide()
            return
        }
        this.loading(true)
        var callback = _.bind(this.responseComplete, this, query)
        var cached = this.cache.get(query)
        if (cached) {
            return callback(cached)
        }
        this.req = $.ajax({
            url: this.endpoint,
            data: this.queryParams(query),
            success: callback,
            failure: _.bind(this.responseError, this, query),
            dataType: 'json'
        })
    },

    responseError: function(query, error) {
        this.loading(false)
    },

    responseComplete: function(query, data) {
        delete this.req
        this.loading(false)
        this.cache.set(query, data)
        if (this.dirty && this.val()) {
            this.query(this.val())
        }
        this.handleResponse(query, data)
    },

    handleResponse: function(query, data) {
        this.render(data)
    },

    getViews: function(items) {
        var views = []
        var renderer = this.renderer
        items = _.first(items, this.maxItems)
        _.each(items, function(item) {
            views.push(new renderer({el: $('<li>'), item: item}))
        })
        return views
    },

    render: function(items) {
        this.selection = -1
        this.hide()
        this.views = this.getViews(items)
        if (!this.views.length) {
            return
        }
        if (!this.$suggestBox) {
            this.$suggestBox = $('<ul>').addClass('suggestbox')
            this.$suggestBox.insertAfter(this.$input)
        } else {
            this.$suggestBox.children().remove()
        }
        this.$suggestBox.width(this.$input.innerWidth())
        var $container = this.$suggestBox
        _.each(this.views, function(view) {
            $container.append(view.render().$el)
        })
        this.$suggestBox.show()
        return this
    }
})

r.ui.SuggestItem = Backbone.View.extend({
    text: function() {
        return ''
    },

    clicked: function() {},

    selected: function() {
        this.$el.addClass('selected')
        return this
    }
})

r.ui.SRItem = r.ui.SuggestItem.extend({
    template: _.template(
        '<span class="name">/r/<%- name %></span><span class="description"><%- description %></span>'
    ),

    text: function() {
        return this.options.item.name
    },

    render: function() {
        this.$el.html(this.template(this.options.item))
        return this
    }
})

r.ui.ClickableSRItem = r.ui.SRItem.extend({
    events: {
        'mouseup': 'clicked'
    },

    clicked: function() {
        window.location = '/r/' + this.options.item.name
    }
})

r.ui.SRSuggest = r.ui.Suggest.extend({
    endpoint: '/api/subreddit_search.json',
    renderer: r.ui.SRItem,
    maxItems: 5,

    handleResponse: function(query, data) {
        this.render(data.subreddits)
    },

    queryParams: function(query) {
        return {query: query, include_over_18: r.config.over_18}
    }
})

r.ui.SRSearchSuggest = r.ui.SRSuggest.extend({
    maxitems: 4,

    setText: function(val) {},

    queryChanged: function(query) {
        if (this.defaultBox) {
            this.defaultBox.query = this.val()
            this.defaultBox.render()
        }
        r.ui.SRSuggest.prototype.queryChanged.apply(this)
    },

    getViews: function(items) {
        var views = r.ui.SRSuggest.prototype.getViews.apply(this, [items])
        if (!this.defaultBox) {
            this.defaultBox = new r.ui.DefaultSearch({el: $('<li>')})
            this.defaultBox.query = this.lastQuery
        }
        if (views.length) {
            views.unshift(this.defaultBox)
        }
        return views
    }
})

r.ui.MultiSuggest = r.ui.SRSuggest.extend({
    split: function(val) {
        return val.split(/([\/+,\s]+(?:r\/)?)/)
    },

    setText: function(val) {
        var values = this.split(this.$input.val())
        var selected = _.isUndefined(this.selected) ? values.length - 1 : this.selected
        values[selected] = val
        var reduced = _.first(values, selected + 1)
        var pos = _.reduce(reduced, function(memo, e) {
            return memo + e.length
        }, 0)
        r.ui.SRSuggest.prototype.setText.apply(this, [values.join('')])
        this.$input.caret(pos)
    },

    val: function() {
        var query = r.ui.SRSuggest.prototype.val.apply(this)
        var pos = this.$input.caret()
        var len = 0
        var selected
        query = _.find(this.split(query), function(e, i) {
            len += e.length
            selected = i
            return len >= pos && !(i % 2)
        })
        this.selected = selected
        return query
    }
})

r.ui.RedditSearchSuggest = r.ui.SRSearchSuggest.extend({
    renderer: r.ui.ClickableSRItem
})

r.ui.DefaultSearch = r.ui.SuggestItem.extend({
    events: {
        'click': 'clicked'
    },
    template: _.template(r.strings('search_default_msg') + '<%- query %>'),

    text: function() {
        return this.query ? this.query : ''
    },

    clicked: function() {
        this.$el.closest('form').submit()
    },

    render: function() {
        this.$el.html(this.template({query: this.text()}))
        return this
    }
})

$(function() {
    $('#search').each(function(idx, el) {
        $(el).data('RedditSearchSuggest', new r.ui.RedditSearchSuggest({el: el}))
    })

    $('.reddit-selector').each(function(idx, el) {
        $(el).data('SRSuggest', new r.ui.SRSuggest({el: el}))
    })

    $('.add-sr').each(function(idx, el) {
        $(el).data('MultiSuggest', new r.ui.MultiSuggest({el: el}))
    })
})
