$(function() {
    // Event handlers for sidebar spoilers prefs.
    $(".spoilerstoggle").submit(function() {
        return post_form(this, 'setspoilersenabled');
    });
    
    $(".spoilerstoggle input").change(function() { $(this).parent().submit(); });
});
