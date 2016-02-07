/*
  Set up actions to run on certain intervals of time

  requires r.config (base.js)

  To add more events to this module to be run, add an
  object to the intervalObjects array in this format:
  {
    name: <name to be used for the r.interval_events.intervalMapping>
    func: <function to be run>
    funcparams: <an array of params to be used when func is run (this seems useless, but can be used if the param can be variable based on multiple factors)> 
    shouldRun: <function to see if the interval should be set, it's recommended to include a r.config.jsintervals.shouldRunp[this.name] check inside>
    timer: <the timing to run on in seconds, recommended to check r.config.jsintervals.timers[this.name] and r.config.jsintervals.timers.default>
  }
  Other attributes can be added and set at will by the
  author of the interval, for whatever use they wish.
  */
!function(r) {
  r.interval_events = {};

  _.extend(r.interval_events, {
    init: function() {
      Function.prototype.bindArray = function(thisArg, args) {
        if (typeof args === "undefined") {
          return this.bind.apply(this, [thisArg]);
        }
        else if (args.constructor === Array) {
          args.unshift(thisArg);
          return this.bind.apply(this, args);
        } else {
          throw TypeError('Function.prototype.bindArray: Arguments list has wrong type')
        }
      }
      r.interval_events.intervalMapping = {};
      var objs = r.interval_events.intervalObjects;
      for (var obj = 0; obj < objs.length; obj++) {
        if (objs[obj].shouldRun()) {
          objs[obj].interval_id = setInterval(objs[obj].func.bindArray(objs[obj], objs[obj].funcparams), objs[obj].timer);
          r.interval_events.intervalMapping[objs[obj].name] = objs[obj].interval_id
        }
      }
    },
    intervalObjects: [{
      name: 'modqueueCounter',
      func: function() {
        r.ajax({
          type: 'GET',
          url: r.config.site_path.concat('/about/modqueue.json?limit=100'),
          success: function(data) {
            var button = $('.reddit-modqueue');
            var counter = $('.special-modqueue-count');
            var newcount = data.data.children.length;
            var newtext = newcount;
            if (data.data.after) {
              newtext += '+';
              if (counter.attr('data-special-modqueue-count') < newcount) {
                button.attr('data-special-modqueue-count', newcount);
                counter.attr('data-special-modqueue-count', newcount);
              }
            } else if (counter.attr('data-special-modqueue-count') != newcount) {
              button.attr('data-special-modqueue-count', newcount);
              counter.attr('data-special-modqueue-count', newcount);
            }
            counter.text(newtext);
          },
          error: function(errorObj) {
            if (errorObj.status == 403) {
              //mod lost permissions, unset interval
              clearInterval(this.interval_id)
            }
          }
        });
      },
      funcparams: [],
      shouldRun: function() {
        return r.config.jsintervals.shouldRun[this.name] && $('.special-modqueue-count');
      },
      timer: r.config.jsintervals.timers[this.name] || r.config.jsintervals.timers.default
    }, {
      name: 'unmoderatedCounter',
      func: function() {
        r.ajax({
          type: 'GET',
          url: r.config.site_path.concat('/about/unmoderated.json?limit=100'),
          success: function(data) {
            var button = $('.reddit-unmoderated');
            var counter = $('.special-unmoderated-count');
            var newcount = data.data.children.length;
            var newtext = newcount;
            if (data.data.after) {
              newtext += '+';
              if (counter.attr('data-special-modqueue-count') < newcount) {
                button.attr('data-special-modqueue-count', newcount);
                counter.attr('data-special-modqueue-count', newcount);
              }
            } else if (counter.attr('data-special-modqueue-count') != newcount) {
              button.attr('data-special-modqueue-count', newcount);
              counter.attr('data-special-modqueue-count', newcount);
            }
            counter.text(newtext);
          },
          error: function(errorObj) {
            if (errorObj.status == 403) {
              //mod lost permissions, unset interval
              clearInterval(this.interval_id)
            }
          }
        });
      },
      funcparams: [],
      shouldRun: function() {
        return r.config.jsintervals.shouldRun[this.name] && $('.special-unmoderated-count');
      },
      timer: r.config.jsintervals.timers[this.name] || r.config.jsintervals.timers.default
    }
  ]});
}(r);
