r.utils = {
    clamp: function(val, min, max) {
        return Math.max(min, Math.min(max, val))
    },

    staticURL: function (item) {
        return r.config.static_root + '/' + item
    },

    querySelectorFromEl: function(targetEl, selector) {
        return $(targetEl).parents().andSelf()
            .filter(selector || '*')
            .map(function(idx, el) {
                var parts = [],
                    $el = $(el),
                    elFullname = $el.data('fullname'),
                    elId = $el.attr('id'),
                    elClass = $el.attr('class')

                parts.push(el.nodeName.toLowerCase())

                if (elFullname) {
                    parts.push('[data-fullname="' + elFullname + '"]')
                } else {
                    if (elId) {
                        parts.push('#' + elId)
                    } else if (elClass) {
                        parts.push('.' + _.compact(elClass.split(/\s+/)).join('.'))
                    }
                }

                return parts.join('')
            })
            .toArray().join(' ')
    },

    serializeForm: function(form) {
        var params = {}
        $.each(form.serializeArray(), function(index, value) {
            params[value.name] = value.value
        })
        return params
    },

    _pyStrFormatRe: /%\((\w+)\)s/,
    pyStrFormat: function(format, params) {
        return format.replace(this._pyStrFormatRe, function(match, fieldName) {
            if (!(fieldName in params)) {
                throw 'missing format parameter'
            }
            return params[fieldName]
        })
    },

    _mdLinkRe: /\[(.*?)\]\((.*?)\)/g,
    formatMarkdownLinks: function(str) {
        return _.escape(str).replace(this._mdLinkRe, function(match, text, url) {
            return '<a href="' + url + '">' + text + '</a>'
        })
    },

    LRUCache: Backbone.Model.extend({
        maxItems: 16,
        cacheIndex: [],
        cache: {},

        set: function(key, data) {
            if(this.cache[key]) {
                var i = _.indexOf(this.cacheIndex, key)
                this.cacheIndex.splice(i, 1)
                this.cacheIndex.push(key)
            } else {
                if(this.cache.length >= this.maxItems) {
                    delete this.cache[this.cacheIndex.shift()]
                }
                this.cache[key] = data
                this.cacheIndex.push(key)
            }
        },

        get: function(key) {
            return this.cache[key]
        }
    })
}
