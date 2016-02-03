/*
  Set up actions to run on certain intervals of time

  requires r.config (base.js)
  */
!function(r) {
  r.interval_events = {};

  _.extend(r.interval_events, {
    init: function() {
      setInterval(
        function() {
          r.ajax({
            type: 'GET',
            url: '/r/testmang/about/modqueue.json',
            success: function(data) {
              var button = $('.reddit-modqueue');
              var counter = $('.special-modqueue-count');
              var newcount = data.data.children.length;
              counter.text(newcount).attr('data-special-modqueue-count', newcount);
              button.attr('data-special-modqueue-count', newcount);
            }
          });
        },
        30000
      );
    }
  });
}(r);
