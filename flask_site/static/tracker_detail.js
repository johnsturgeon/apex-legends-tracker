/**
 * Sets the detail information for a given tracker
 * @param  {String} legend_name Name of the legend, i.e. Bangalore.
 * @param  {String} label_value Name of the label (typically the same as the legend)
 * @param  {String} tracker_key Tracker key, i.e. 'damage', 'wins'
 * @param  {Number} count Total for *that* tracker for *that* legend
 * @param  {Number} total Total for *that* tracker for this specific legend
 * @param  {String} tracker_state State of the tracker: MISSING, OLD, CURRENT
 * @param  {String} legend_tracker_state Worst state of the aggregate of all the trackers
 * @return {[type]}      [description]
 */
function setTrackerDetails(
    legend_name,
    label_value,
    tracker_key,
    count,
    total,
    tracker_state,
    legend_tracker_state
) {
    let withPercent = 0
    if (count > 0) {
        withPercent = Math.ceil((count / total) * 100)
    }
    const percentString = withPercent.toString() + '%'
    const formattedTotal = total.toLocaleString()
    const progress_bar = $("#tracker-detail-progress-bar-" + legend_name + "-" + tracker_key)
    const progress_container = $("#tracker-detail-progress-container-" + legend_name + "-" + tracker_key)
    if (legend_tracker_state === "MISSING") {
        progress_container.removeClass("progress-bar-tracker-state-current")
        progress_container.removeClass("progress-bar-tracker-state-old")
        progress_container.addClass("progress-bar-tracker-state-missing")
    } else if (legend_tracker_state === "OLD") {
        progress_container.removeClass("progress-bar-tracker-state-current")
        progress_container.removeClass("progress-bar-tracker-state-missing")
        progress_container.addClass("progress-bar-tracker-state-old")
    } else {
        progress_container.removeClass("progress-bar-tracker-state-old")
        progress_container.removeClass("progress-bar-tracker-state-missing")
        progress_container.addClass("progress-bar-tracker-state-current")
    }

    $("#tracker-detail-lr-style-label-" + legend_name + "-" + tracker_key).text(label_value)
    $("#tracker-detail-lr-style-count-" + legend_name + "-" + tracker_key).text(count)
    $("#tracker-detail-lr-style-total-" + legend_name + "-" + tracker_key).text(total)
    progress_bar.width(percentString)
    $("#circle-total-any-" + tracker_key).text(formattedTotal)
    $("#circle-total-subtext-any-" + tracker_key).text(tracker_state)
}

/**
 * updates all the tracker totals
 * @param  {String} tracker_key The tracker key
 * @param  {Object} tracker_totals total json object
 */
function updateAllTrackers(tracker_key, tracker_totals) {
    const total_for_tracker = tracker_totals.total
    console.log("tracker state: " + tracker_totals.tracker_state)
    tracker_state_string = stringForState(tracker_totals.tracker_state)
    legends = tracker_totals.legends
    for (let i = 0; i < legends.length; i++) {
        legend = legends[i]
        console.log(legend)
        legend_state_string = stringForState(legend.tracker_state)
        setTrackerDetails(
            legend.name,
            legend.name,
            tracker_key,
            legend.total,
            total_for_tracker,
            tracker_state_string,
            legend_state_string
        )
    }
}

function stringForState(tracker_state) {
    let tracker_state_string = ""
    console.log("stringForState: " + tracker_state)
    switch (tracker_state) {
        case "-1":
            tracker_state_string = "MISSING"
            break
        case "0":
            tracker_state_string = "OLD"
            break
        case "1":
            tracker_state_string = "CURRENT"
            break
        default:
            tracker_state_string = "NO_DATA"
    }
    console.log(tracker_state_string)
    return tracker_state_string
}

/**
 * Pulls current tracker data from the DB and updates the fields
 * @param  {[Number]} player_uid [UID of the player]
 * @param  {String} tracker_key [key for the tracker]
 */
function refreshTracker(player_uid, tracker_key) {
    $.getJSON($SCRIPT_ROOT + '/_get_tracker_data', {
        player_uid: player_uid,
        tracker_key: tracker_key
    }, function(data) {
        updateAllTrackers(tracker_key, data.tracker_totals)
    })
}

/**
 * Sets the default values for all the trackers while the data is loading
 */
function setDefaultValues() {
    setTrackerDetails(
        "Legend",
        "Loading...",
        "loading",
        0,
        0,
        "MISSING",
        "MISSING"
    )
}


