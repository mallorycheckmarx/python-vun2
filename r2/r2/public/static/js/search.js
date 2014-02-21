r.ui.SuggestItems = Backbone.Collection.extend({
    endpoint: '/',

    initialize: function() {
        this.cache = new r.utils.LRUCache()
    },

    queryParams: function(query) {
        return {query: query}
    },

    extractModels: function(query, data) {
        return []
    },

    responseError: function(query, xhr, textStatus, errorThrown) {
        delete this.req
        this.trigger('error', [query, textStatus, errorThrown])
    },

    responseComplete: function(query, data) {
        delete this.req
        this.reset(this.extractModels(query, data))
    },

    query: function(query) {
        this.req = this.cache.ajax(query, {
            url: this.endpoint,
            data: this.queryParams(query),
            dataType: 'json'
        }).done(_.bind(this.responseComplete, this, query))
          .fail(_.bind(this.responseError, this, query))
    },

    abort: function() {
        if (this.req && this.req.abort) {
            this.req.abort()
        }
    }
})

r.ui.SuggestItem = Backbone.View.extend({
    queryText: function() {
        return ''
    },

    action: function() {},

    select: function() {
        this.$el.addClass('selected')
        return this
    }
})

r.ui.Suggest = Backbone.View.extend({
    collectionClass: r.ui.SuggestItems,
    viewClass: r.ui.SuggestItem,
    requestThrottleTimeout: 333,

    events: {
         'keydown .suggestfield': 'keyDown',
         'keyup .suggestfield': 'keyUp',
         'input .suggestfield': 'inputEvent',
         'click .suggestfield': 'queryChanged',
         'blur .suggestfield': 'defocused',
         'mouseout .suggestbox li': 'itemHoverOut',
         'mouseover .suggestbox li': 'itemHover',
         'mousedown .suggestbox li': 'itemMouseDown',
         'click .suggestbox li': 'itemClick',
         'click #suggested-reddits a': 'popularRedditClick',
         'click': 'areaClicked',
         'focus .suggestfield': 'show'
    },

    initialize: function() {
        this.$expando = this.$el.find('#searchexpando')
        this.$el.addClass('suggestarea')
        this.$input = this.$el.find('input').first()
            .addClass('suggestquery')
            .attr('autocomplete', 'off')
        this.selectionIndex = -1
        this.suggest = _.throttle(this._suggest, this.requestThrottleTimeout)
        this.collection = new this.collectionClass()
        this.collection.on("change reset add remove error", this.update, this)
    },

    areaClicked: function() {},

    checkfocus: function() {
        if (!this.$input.is(':focus')) {
            this.hide()
            this.stop()
        }
    },

    defocused: function() {
        // Allows for refocusing in a small amount of time
        // for an example, on click of advanced search.
        setTimeout(_.bind(this.checkfocus, this), 250)
    },

    inputEvent: function() {
        this.ready = true
        this.queryChanged()
    },

    popularRedditClick: function(e) {
        e.preventDefault()
        this.setText($(e.target).text())
    },

    setText: function(val) {
        this.$input.val(val)
    },

    query: function() {
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

    /* Prevent text selection oddities when clicking items in the list */
    itemMouseDown: function(e) {
        e.preventDefault()
    },

    itemClick: function(e) {
        var $item = $(e.currentTarget)
        this.selectionIndex = $item.index()
        this.setText(this.views[this.selectionIndex].queryText())
        this.stop()
        this.hide()
    },

    stop: function() {
        this.collection.abort()
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
        this.selectionIndex = $item.index()
        this.views[this.selectionIndex].select()
    },

    changeSelectionBy: function(difference) {
        this.deselectAll()
        var index = this.selectionIndex + difference + 1
        var size = this.size() + 1
        this.selectionIndex = ((index + size) % size) - 1
        if (this.selectionIndex < 0) {
            this.setText(this.lastQuery)
        } else {
            this.setText(this.views[this.selectionIndex].select().queryText())
        }
    },

    keyUp: function(e) {
        // enter
        if (e.keyCode == 13) {
            if (this.selectionIndex >= 0) {
                e.preventDefault()
                this.views[this.selectionIndex].action()
                this.stop()
                this.hide()
            }
        // left or right
        } else if (e.keyCode == 37 || e.keyCode == 39) {
            this.queryChanged()
        // backspace
        } else if (e.keyCode == 8) {
            this.queryChanged()
        }
    },

    keyDown: function(e) {
        if (!this.visible()) {
            return
        }
        // up or down
        if (e.keyCode == 38 || e.keyCode == 40) {
            e.preventDefault()
            this.changeSelectionBy(e.keyCode == 38 ? -1 : 1)
        // enter
        } else if (e.keyCode == 13) {
            // Prevent default so we may handle this on keyup without submitting the form
            if (this.selectionIndex >= 0) {
                e.preventDefault()
            }
        }
    },

    queryChanged: function() {
        var query = $.trim(this.query())
        if (!query) {
            this.stop()
            this.hide()
        }
        if (query != this.lastQuery) {
            this.suggest(query)
        }
    },

    show: function() {
        this.suggest(this.query())
    },

    hide: function() {
        if (this.$suggestBox) {
            this.$expando.css("margin-top", 0)
            this.$suggestBox.hide()
        }
    },

    loading: function(done) {
        if (!_.isUndefined(done)) {
            this.$el.toggleClass('working', done)
            return this
        } else {
            return this.$el.hasClass('working')
        }
    },

    _suggest: function(query) {
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
        this.collection.query(query)
    },

    getViews: function(items) {
        var views = []
        var viewClass = this.viewClass
        items = _.first(items, this.maxItems)
        _.each(items, function(item) {
            views.push(new viewClass({el: $('<li>'), item: item}))
        })
        return views
    },

    update: function() {
        this.loading(false)
        if (this.dirty && this.query()) {
            this.query(this.query())
        }
        this.render()
    },

    render: function() {
        this.selectionIndex = -1
        this.hide()
        this.views = this.getViews(this.collection.models)
        if (!this.views.length) {
            return
        }
        if (!this.$suggestBox) {
            this.$suggestBox = $('<ul>').addClass('suggestbox')
            this.$suggestBox.insertAfter(this.$input)
        } else {
            this.$suggestBox.empty()
        }
        this.$suggestBox.width(this.$input.innerWidth())
        var $container = this.$suggestBox
        _.each(this.views, function(view) {
            $container.append(view.render().$el)
        })
        this.$suggestBox.show()
        this.$expando.css("margin-top", this.$suggestBox.height() + 'px')
        return this
    }
})

r.ui.SRModel = Backbone.Model.extend({})

r.ui.SRItem = r.ui.SuggestItem.extend({
    template: _.template(
        '<span class="name">/r/<%- name %></span><div class="description"><%- description %></div>'
    ),

    queryText: function() {
        return this.options.item.get('name')
    },

    render: function() {
        this.$el.html(this.template(this.options.item.attributes))
        return this
    }
})

r.ui.ClickableSRItem = r.ui.SRItem.extend({
    template: _.template(
        'go to <span class="name">/r/<%- name %></span><span class="description"><%- description %></span>'
    ),

    events: {
        'click': 'action'
    },

    action: function(e) {
        window.location = '/r/' + this.options.item.get('name')
    }
})

r.ui.SRItems = r.ui.SuggestItems.extend({
    endpoint: '/api/subreddit_search.json',

    queryParams: function(query) {
        return {query: query, include_over_18: r.config.over_18}
    },

    extractModels: function(query, data) {
        var models = []
        _.each(data.subreddits, function(item) {
            models.push(new r.ui.SRModel(item))
        })
        return models
    }
})

r.ui.SRSuggest = r.ui.Suggest.extend({
    collectionClass: r.ui.SRItems,
    viewClass: r.ui.SRItem,
    maxItems: 5
})

r.ui.SRSearchSuggest = r.ui.SRSuggest.extend({
    maxItems: 4,

    areaClicked: function() {
        // Allows for refocus after click on advanced search
        this.$input.focus()
    },

    itemClick: function() {},

    setText: function() {},

    queryChanged: function(query) {
        if (this.defaultBox) {
            this.defaultBox.query = this.query()
            this.defaultBox.render()
        }
        r.ui.SRSuggest.prototype.queryChanged.call(this)
    },

    getViews: function(items) {
        var views = r.ui.SRSuggest.prototype.getViews.call(this, items)
        this.defaultBox = new r.ui.DefaultSearch({el: $('<li>')})
        this.defaultBox.query = this.lastQuery
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

    findSelected: function(query) {
        var len = 0
        var selected
        var pos = this.$input.caret()
        query = _.find(this.split(query), function(elem, idx) {
            len += elem.length
            selected = idx
            // Only odd as we want to select the non-separator portion
            return len >= pos && !(idx % 2)
        })
        this.selected = selected
        return query
    },

    setText: function(val) {
        var query = this.$input.val()
        var values = this.split(query)
        this.findSelected(query)
        values[this.selected] = val
        var pos = r.utils.sumLength(_.first(values, this.selected + 1))
        r.ui.SRSuggest.prototype.setText.call(this, values.join(''))
        this.$input.caret(pos)
    },

    query: function() {
        var query = r.ui.SRSuggest.prototype.query.call(this)
        return this.findSelected(query)
    }
})

r.ui.RedditSearchSuggest = r.ui.SRSearchSuggest.extend({
    viewClass: r.ui.ClickableSRItem
})

r.ui.DefaultSearch = r.ui.SuggestItem.extend({
    events: {
        'click': 'action'
    },
    template: _.template('<span>' + r._('Search for: ') + '<%- query %>' + '</span>'),

    queryText: function() {
        return this.query ? this.query : ''
    },

    action: function() {
        console.log("WTF!!!")
        this.$el.closest('form').submit()
    },

    render: function() {
        this.$el.html(this.template({query: this.queryText()}))
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
