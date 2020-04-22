function changeSearch(event) {
    if ($("#line_search").val().length > 0) {
        $.ajax('/line/'+$("#line_search").val(), {
            success : writeList
        })
      }
}

function writeList(data, status) {
    validIds = []
    /* Add them all, as neccesary */
    $.each(data.object_list, function (i, line) {
        validIds.push('l'+line.pk)
          if (!$('#l'+line.pk).length) {
            if (line.publiclinenumber) { // not all lines with a lineplanningnumber has a publiclinenumber or headsign
                if (line.publiclinenumber != line.lineplanningnumber) {
                    row = '<tr class="line" id="l'+line.pk+'"><td>'+line.publiclinenumber+ ' / ' + line.lineplanningnumber+'</td>';
                } else {
                    row = '<tr class="line" id="l'+line.pk+'"><td>'+line.publiclinenumber+'</td>';
                }
                row += '<td>'+line.headsign+'</td></tr>';
                $(row).hide().appendTo("#rows").fadeIn(999);
            }
          }
    });

    /* Cleanup */
    $("#rows tr").each(function(index) {
        if ($.inArray($(this).attr('id'), validIds) == -1) {
            $(this).fadeOut(999).remove()
        }
    });
}

/* TRIP SELECTION */
var selectedTrips = [];
var activeJourneys = [];
var activeLine = null;
var cancelledLines = [];
var currentLineMeasures = null;

function showTrips(event) {
    $("#rows tr.success").removeClass('success');
    $(".suc-icon").remove();
    var operating_day = $("#id_operatingday").val();

    $(this).children('td').eq(1).append('<span class="suc-icon pull-right glyphicon glyphicon-arrow-right"></span>');
    activeLine = $(this).attr('id').substring(1);

    showTripsOnChange();

    $('#line').val(activeLine)
    $(this).addClass('success')
}

function removeTripFromX(event, ui) {
    removeTrip($(this).parent().attr('id').substring(2));
}

function removeTrip(ritnr) {
    var id = $.inArray(ritnr, selectedTrips);
    if (id != -1) {
        $('#t'+ritnr).removeClass('success');
        $('#st'+ritnr).remove();
        selectedTrips.splice(id, 1);
    }
    if (selectedTrips.length == 0) {
        $('#rit-list .help').show();
    }
    writeTripList();
}

function loadPreselectedJourneys() {
    $(".rit-preload").each(function(id, val) {
        selectedTrips.push($(val).attr('id').substring(2));
    });
    writeTripList();
}

function selectTrip(event, ui) {
    var ritnr = $(ui.selected).attr('id').substring(1);
    if ($.inArray(parseInt(ritnr), activeJourneys) != -1 /* Note our array stores numbers, so convert */
        || $(ui.selected).hasClass("line_warning")) /* TODO: ritnr array selection faster than class selection? This disables trip that have been line cancelled. */
        return;

    var id = $.inArray(ritnr, selectedTrips);
    if (id == -1) {
        $('#rit-list .help').hide();
        $(ui.selected).addClass('success');
        var label = $(ui.selected).find("strong").text();
        var dellink = '<span class="trip-remove glyphicon glyphicon-remove"></span>';
        $('#rit-list').append('<span id="st'+ritnr+'" class="pull-left trip-selection label label-danger">'+label+' '+dellink+'</span>');
        selectedTrips.push(ritnr);
        writeTripList();
    } else {
        removeTrip($(ui.selected).attr('id').substring(1));
    }
}

function writeTripList() {
    var out = "";
    $.each(selectedTrips, function(index, val) {
        out += val+',';
    });
    $("#journeys").val(out)
}

function changeOperatingDayTrips() {
    $("#rit-list span").remove();
    $('#rit-list .help').show();
    selectedTrips = [];
    activeJourneys = [];
    $("#journeys").val('');
    getActiveLines();
    var operating_day_text = $("#id_operatingday option:selected" ).text();
    $("#operating_day_text").text(operating_day_text);
}

function getActiveLines() {
    var operating_day = $("#id_operatingday").val();
    if (operating_day != null) {
        $.ajax({ url: '/lijnaanpassing/lijnen.json',
            data: {'operatingday': operating_day},
            success : saveLines
        });
    } else {
        cancelledLines = [];
        $('#trips thead').hide();
        $('#trips tbody').addClass('empty_database');
        $('#trips tbody').text("Er staan geen ritten in de database.");
    }
}

function saveLines(data, status) {
    if (data.object) {
        cancelledLines = data.object;
    } else {
        cancelledLines = [];
    }
    getActiveJourneys();
}

function getActiveJourneys() {
    var operating_day = $("#id_operatingday").val();
     $.ajax({ url: '/ritaanpassing/ritten.json',
            data: {'operatingday': operating_day},
            success : writeActiveJourneys
     });
}

function writeActiveJourneys(data, status) {
    if (data.object) {
        $.each(data.object, function (i, journey) {
            activeJourneys.push(journey.id)
        });
    }
    showTripsOnChange();
}

function showTripsOnChange() {
    if (activeLine != null) {
        currentLineMeasures = cancelledLines.filter(l => l.id == activeLine || l.id === null);

        var operating_day = $("#id_operatingday").val();

        $.ajax({ url: '/line/'+activeLine+'/ritten',
         data: {'operatingday': operating_day},
            success : writeTrips
        });
    }
}

function writeTrips(data, status) {
    maxLen = Math.max(data.object.trips_1.length, data.object.trips_2.length)
    if (maxLen > 0) {
        $('#trips tbody').fadeOut(200).empty();
        tripRows = null;

        for (i = 0; i <= maxLen; i = i + 1) {
            a = null;
            b = null;
           if (i in data.object.trips_1)
               a = data.object.trips_1[i];
           if (i in data.object.trips_2)
              b = data.object.trips_2[i];
           tripRows += renderTrip(a, b);
        }
        $('#trips tbody').append(tripRows)
        $('#trips thead').fadeIn(200);
        $('#trips tbody').fadeIn(200);
    } else {
        $('#trips thead').hide();
        $('#trips tbody').text("Geen ritten in database.");
    }
}

function renderTrip(trip_a, trip_b) {
    out = '<tr>';
    out += renderTripCell(trip_a);
    out += renderTripCell(trip_b);
    out += '</tr>';
    return out
}

function renderTripCell(trip) {
    if (trip == null)
        return "<td>&nbsp;</td>";

    $('#trips td.warning').removeClass('warning');
    $('#trips td.line_warning').removeClass('line_warning');

    const currentTripMeasures = currentLineMeasures.filter(measure => {

        if (measure.begintime === null && measure.endtime === null) {
            return true;
        } else if (measure.begintime === null && measure.endtime > trip.departuretime) {
            return true;
        } else if (measure.begintime <= trip.departuretime && measure.endtime === null) {
            return true;
        } else if (measure.begintime <= trip.departuretime && measure.endtime >= trip.departuretime) {
            return true;
        }

    });

    if ($.inArray(trip.id, activeJourneys) != -1) {
        out = '<td class="trip warning" id="t'+trip.id+'">'
    } else if (currentTripMeasures.length > 0) {
        out = '<td class="trip line_warning" id="t'+trip.id+'">'
    } else {
        out = '<td class="trip" id="t'+trip.id+'">'
    }
    out += "<strong>Rit "+trip.journeynumber+"</strong>"
    out += "&nbsp;<small>Vertrek "+convertSecondsToTime(trip.departuretime)+"</small>"
    if ($.inArray(trip.id, activeJourneys) != -1) {
        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Rit is al opgeheven"></span>'
    }
    if (currentTripMeasures.length > 0) {
        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Lijn is al opgeheven"></span>'
    }
    out += "</td>"
    return out
}

function convertSecondsToTime(seconds) {
    var hours   = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds - (hours * 3600)) / 60);
    var extra = "";
    if (hours > 23) {
        hours = hours - 24
        extra = " <em>(+1)</em>"
    }
    return ""+padTime(hours)+":"+padTime(minutes)+extra;
}

function padTime(i) {
    str = i.toString()
    if (str.length == 2) {
        return str;
    } else if (str.length == 1) {
        return '0'+str;
    } else {
        return '00';
    }
}

function notMonitored() {
    //var selected_item = $(".dropdown-menu").on('click', 'li a', notMonitored);

    $("#notMonitored").text($(this).text());
    $("#notMonitoredInput").val($(this).attr('value'));

    // $(this).parents(".btn-group").find('.disabled').html($(this).text());
    // $(this).parents(".btn-group").find('.disabled').val($(this).data('value'));
    //$(this).parents(".btn-group").find('.disabled').val($(this));
    $("#notMonitored").removeClass('disabled');
}