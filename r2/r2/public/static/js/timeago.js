r.timeago = {

    init: function() {

        /* Load fuzzy time i18n strings */
        $.timeago.settings.strings = {
            prefixAgo: null,
            prefixFromNow: null,
            suffixAgo: r.strings.ta_ago,
            suffixFromNow: r.strings.ta_suffixFromNow,
            seconds: r.strings.ta_seconds,
            minute: r.strings.ta_minute,
            minutes: r.strings.ta_minutes,
            hour: r.strings.ta_hour,
            hours: r.strings.ta_hours,
            day: r.strings.ta_day,
            days: r.strings.ta_days,
            month: r.strings.ta_month,
            months: r.strings.ta_months,
            year: r.strings.ta_year,
            years: r.strings.ta_years
        };
        
        /* Init fuzzy time on time elements */
        $("time.fuzzy-time").timeago();
    }
}
