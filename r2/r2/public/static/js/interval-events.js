/*
  Set up actions to run on certain intervals of time

  requires r.config (base.js)
  */
!function(r) {
  r.interval_events = {};

  _.extend(r.interval_events, {
    init: function() {
      Function.prototype.bindArray = function(thisArg, args) {
          args.unshift(thisArg);
          return this.bind.apply(this, args)
      }
      var objs = r.interval_events.intervalObjects;
      for (var obj = 0; obj < objs.length; obj++) {
        if (objs[obj].shouldRun()) {
          if (objs[obj].funcparams) {
            objs[obj].as_interval = setInterval(objs[obj].func.bindArray(objs[obj], objs[obj].funcparams), objs[obj].timer);
          } else {
            objs[obj].as_interval = setInterval(objs[obj].func.bind(objs[obj]), objs[obj].timer);
          }
        }
      }
    },
    intervalObjects: [{
      name: 'modqueueCounter',
      func: function() {
        r.ajax({
          type: 'GET',
          url: r.config.site_path.concat('/about/modqueue.json'),
          success: function(data) {
            var button = $('.reddit-modqueue');
            var counter = $('.special-modqueue-count');
            var newcount = data.data.children.length;
            counter.text(newcount).attr('data-special-modqueue-count', newcount);
            button.attr('data-special-modqueue-count', newcount);
          },
          error: function(errorObj) {
            if (errorObj.status == 403) {
              //mod lost permissions, unset interval
              clearInterval(this.as_interval)
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
          url: r.config.site_path.concat('/about/unmoderated.json'),
          success: function(data) {
            var button = $('.reddit-unmoderated');
            var counter = $('.special-unmoderated-count');
            var newcount = data.data.children.length;
            counter.text(newcount).attr('data-special-unmoderated-count', newcount);
            button.attr('data-special-unmoderated-count', newcount);
          },
          error: function(errorObj) {
            if (errorObj.status == 403) {
              //mod lost permissions, unset interval
              clearInterval(this.as_interval)
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
