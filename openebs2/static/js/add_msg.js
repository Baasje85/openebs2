/* STOP AND SCENARIO FUNCTIONS */
var selectedStops = []
var scenarioStops = []
var blockedStops = [] /* Already have messages set */
var line_related = document.getElementById('lijngebonden').checked;
var currentLine = null; //  lineplanningnumber
var lineSelectionOfStop = {};
var lineSelection = [];
var halteList = [];

function changeSearch(event) {
    if ($("#line_search").val().length > 0) {
        $.ajax('/line/'+$("#line_search").val(), {
            success : writeList
        })
    }
}

function changeCount(event) {
    len = $(this).val().length
    addon = $(this).parents('.countwrapper').find('.charcount')[0]
    $(addon).text(len);
    $(addon).removeClass('badge-success badge-warning badge-danger')
    if (len < 178) {
       $(addon).addClass('badge-success')
    } else if (len > 177 && len < 250) {
       $(addon).addClass('badge-warning')
    } else if (len > 249) {
       $(addon).addClass('badge-danger')
    }
}

function writeList(data, status) {
    validIds = []
    /* Add them all, as neccesary */
    $.each(data.object_list, function (i, line) {
        validIds.push('l'+line.pk)
        if (!$('#l'+line.pk).length) {
            if (line.publiclinenumber) { // not all lines with a lineplanningnumber has a publiclinenumber or headsign
                var out = '';
                var row = '';
                if (line.publiclinenumber != line.lineplanningnumber) {
                out += "<strong>"+line.publiclinenumber+"</strong>";
                out += " / ";
                out += "<small>"+line.lineplanningnumber+"</small>";
                    row = '<tr class="line" id="l'+line.pk+'"><td>'+out+'</td>';
                } else {
                    out += "<strong>"+line.publiclinenumber+"</strong>";
                    out += '<span class="hidden"><small>'+line.lineplanningnumber+'</small>'
                    row = '<tr class="line" id="l'+line.pk+'"><td>'+out+'</td>';
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

function showStops(event) {
    $("#rows tr.success").removeClass('success');
    $(".suc-icon").remove();
    $(this).children('td').eq(1).append('<span class="suc-icon pull-right glyphicon glyphicon-arrow-right"></span>');
    $.ajax('/line/'+$(this).attr('id').substring(1)+'/stops', {
        success : writeLine
    })
    $(this).addClass('success')
    currentLine = $('#rows tr.success').find("small").text();
}

function selectStop(event, ui) {
    $('#halte-list .help').hide();
    if (doSelectStop(ui.selected)) {
        writeHaltesField();
    }
}

function selectStopFromBall(obj) {
    $('#halte-list .help').hide();
    var did = false
    var parent = $(this).parents('.stopRow');
    var left = $(parent).find(".stop-left");
    var right = $(parent).find(".stop-right");
    if (left.length) {
        doSelectStop(parent.find(".stop.stop-right"));
        did = true;
    }
    /* Check if left and right stops aren't accidentally equal */
    if (left.length && right.length && left.attr('id').slice(0, -1) != right.attr('id').slice(0, -1)) {
        doSelectStop(parent.find(".stop.stop-left"));
        did = true;
    }
    if (did) {
        writeHaltesField();
    }
}

function selectAllVisibleStops() {  // TODO: take current line into account
    $('#halte-list .help').hide();
    $('#stops .stop').each(function(index, value) {
        /* Check this is not already selected */
        index = $(this).attr('id').slice(0, -1) + "-" + currentLine;
        if ($.inArray(index, selectedStops) == -1) {
            doSelectStop($(this));
        }
    });
    writeHaltesField();
}

function deselectAllVisibleStops() {  // TODO: take current line into account
    var line = currentLine;
    // $('#halte-list .help').show();
    // $('#stops .stop.success').each(function(index, value) {
    //    index = $(this).attr('id').slice(0, -1);
    //    var new_id = index + '-' + currentLine;
    //    if ($.inArray(new_id, selectedStops) != -1) {
    //        removeStop(new_id, currentLine)
    //    }
    //});
    var id = $.inArray(line, lineSelection);
    lineSelection.splice(id, 1);
    removeStop('all', line);
    writeHaltesField();
}

function doSelectStop(obj) {  // TODO: take current line into account
    /* Make sure to strip the 'l' or 'r' */
    var id = $(obj).attr('id').slice(0, -1);
    var new_id = id + '-' + currentLine;
    var index = $.inArray(new_id, selectedStops);
    if (index == -1) {
        $("#"+id+"l, #"+id+"r").addClass('success');
        $("#"+id+"l, #"+id+"r").append('<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;');
        selectedStops.push(new_id);

        var selectedLines = [];
        if (lineSelectionOfStop[id] !== undefined) {
            selectedLines = lineSelectionOfStop[id];
        }
        selectedLines.push(currentLine);
        lineSelectionOfStop[id] = selectedLines;
        var i = $.inArray(currentLine, lineSelection);
        if (i == -1) {
            lineSelection.push(currentLine);
        }

        if ($(obj).hasClass('stop-left')) {
            direction = "heen";
        } else {
            direction = "trg";
        }
        delLink = '<span class="stop-remove glyphicon glyphicon-remove"></span>';
        var text = $(obj).text()+'('+direction+') ';
        halteList.push([text, currentLine]);
        if (line_related) {
            writeHaltesWithLine();
        } else {
            writeHaltesWithoutLine();
        }
        return true;
    } else {
        removeStop(id, currentLine);
    }

    return false;
}

/* Write data to the form field */
function writeHaltesField() {
    var out = "";
    var stops = [];
    if (line_related) {
        writeLineOutputAsString(lineSelection);
    } else {
        $.each(selectedStops, function(i, stop) {
            if (stop !== undefined) {
                var stop_id = stop.split("-")[0].substring(1);
                if ($.inArray(stop_id, stops) === -1) {
                    stops.push(stop_id);
                }
            }
        });
        $.each(stops, function(index, halte) {
            out += halte+",";
        });
        $("#haltes").val(out);
    }
}

/* Do the inverse in case we're editing or something */
function readHaltesField() {  // TODO: take current line into account
    $.each($("#haltes").val().split(','), function(i, halte) {
        if (halte != "") {
            selectedStops.push('s'+halte)
        }
    });
}

/* Wrapper functions to get the id */
function selectionRemoveStop(event) {
    removeStop($(this).parent().attr('id').substring(1), currentLine)  // TODO check if correct line!
}

function lineRemoveStop(event) {
    removeStop($(this).attr('id').slice(0, -1), currentLine) // TODO check if correct line!
}

/* Do the actual work here */
function removeStop(id, line) {  // TODO: take current line into account
    if (id == 'all') {
        //$.each(selectedStops, function(i, stop) {
        //    if (stop.split('-')[1] == line) {
        //}
        for (var i = 0; i < selectedStops.length; i++) {
            if (selectedStops[i].split('-')[1] == line) {
                // $("#s"+selectedStops[i]).remove();
                // if stop from current line:
                if (line === currentLine) {
                    var old_id = selectedStops[i].split('-')[0];
                    $("#"+old_id+"l, #"+old_id+"r").removeClass('success');
                    $("#"+old_id+"l .stop-check, #"+old_id+"r .stop-check").remove();
                }
                selectedStops.splice(i, 1);
                i--;
            }
        }
        removeStopFromDict(id, line);
        removeStopFromHalteList(id, line);
    } else {
        var old_id = id.split('-')[0];
        var i = $.inArray(id, selectedStops);
        if (i != -1) {
            selectedStops.splice(i, 1);
            removeStopFromDict(id, line);
            $("#s"+id).remove(); // CMB: removes from 'halte-list'
            // if stop from current line:
            if (line === currentLine) {
                $("#"+old_id+"l, #"+old_id+"r").removeClass('success')
                $("#"+old_id+"l .stop-check, #"+old_id+"r .stop-check").remove()
            }
        }
    }
    if (line_related) {
        writeHaltesWithLine();
    } else {
        writeHaltesWithoutLine();
    }
    writeHaltesField()
}

function removeStopFromHalteList(id, line) {
    if (id == 'all') {
        for (var i = 0; i < halteList.length; i++) {
            if (halteList[i][1] == line) {
                    halteList.splice(i, 1);
                    i--;
            }
        }
    }
    //else {
        // TODO nog ff uitvogelen
    //}
}

function writeLine(data, status) {
    $('#stops').fadeOut(200).empty();
    out = ""
    $.each(data.object.stop_map, function (i, stop) {
        out += renderRow(stop)
    });
    $('#stops').append(out)
    $('#stops').fadeIn(200);
    $('.stop_btn').removeClass('hide');
}

function renderRow(row) { // TODO: take current line into account + times of existing messages
    out = '<tr class="stopRow">';
    if (row.left != null) {
        if ($.inArray(row.left.id, scenarioStops) != -1) {
            out += '<td class="warning">'+row.left.name+' <span class="glyphicon glyphicon-warning-sign pull-right" title="Al in scenario opgenomen"></span></td>'
        } else {
            var id = 's'+row.left.id+'l';
            if ($.inArray('s'+row.left.id+'-'+currentLine, selectedStops) != -1) {
                out += '<td class="stop stop-left success" id="'+id+'">'+row.left.name+'<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;'
            } else {
                out += '<td class="stop stop-left" id="'+id+'">'+row.left.name;
                if ($.inArray(row.left.id, blockedStops) != -1) {
                    out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al bericht"></span>'
                }
                out += '</td>';
            }
        }
    } else {
        out += '<td>&nbsp;</td>';
    }
    if (row.left != null && row.right != null) {
        out += '<td class="img text-center"><img class="stop-img stop-both" src="/static/img/stop-both.png"></td>'
    } else if (row.left != null) {
        out += '<td class="img text-center"><img class="stop-img stop-left" src="/static/img/stop-left.png"></td>'
    } else if (row.right != null) {
        out += '<td class="img text-center"><img class="stop-img stop-right" src="/static/img/stop-right.png"></td>'
    }
    if (row.right != null) {
        if ($.inArray(row.right.id, scenarioStops) != -1) {
            out += '<td class="warning">'+row.right.name+' <span class="glyphicon glyphicon-warning-sign pull-right" title="Al in scenario opgenomen"></span></td>'
        } else {
            var id = 's'+row.right.id+'r';
            if ($.inArray('s'+row.right.id+'-'+currentLine, selectedStops) != -1) {
                out += '<td class="stop stop-right success" id="'+id+'">'+row.right.name+'<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;</td>';
            } else {
                out += '<td class="stop stop-right" id="'+id+'">'+row.right.name;
                if ($.inArray(row.right.id, blockedStops) != -1) {
                    out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al bericht"></span>'
                }
                out += '</td>';
            }
        }
    } else {
        out += '<td>&nbsp;</td>';
    }
    out += '</tr>';
    return out
}

function getScenarioStops(scenario) {
     $.ajax('/scenario/'+scenario+'/haltes.geojson', {
            success : writeScenarioStops
     })
}

function writeScenarioStops(data, status) {
    if (data.features) {
        $.each(data.features, function (i, halte) {
            stop = halte['properties']['dataownercode']+ '_' + halte['properties']['userstopcode']
            scenarioStops.push(stop)
        });
    }
}

function getHaltesWithMessages() {  // TODO: take line into account (if set)
    $.ajax('/bericht/haltes.json', {
            success : writeHaltesWithMessages
     })
}

function writeHaltesWithMessages(data, status) {  // TODO: take line into account (if set)
    $.each(data.object, function (i, halte) {
        stop = halte['dataownercode']+ '_' + halte['userstopcode']
        blockedStops.push(stop)
    });
}

function lineRelated() {
  line_related = document.getElementById('lijngebonden').checked;
  $('#line_related').val(line_related);
  switchHaltesField();
}

function switchHaltesField() {
    if (line_related) {
        $('#halte-list span').remove();
        writeHaltesWithLine();
    } else {
        $('#halte-list div').remove();
        $('#lines').val('');
        writeHaltesWithoutLine();
    }
    writeHaltesField();
}

function writeHaltesWithLine() {
    $('#halte-list div').remove();
    $.each(lineSelection, function (index, line) {
        $("#halte-list").append('<div><p class=lijn'+line+' id=lijn'+line+'><label class=pull-left>Lijn: '+line+'</label></p><br /></div><div class="clearfix" id="lijnfix"></div>');
    });
    var delLink = '<span class="stop-remove glyphicon glyphicon-remove"></span>';
    $.each(halteList, function(i, stop) {
        var halte = stop[0];
        var lijn = stop[1];
        $('.lijn'+lijn).append('<span class="stop-selection pull-left label label-primary" id="s'+halte+'">'+halte+delLink+'</span');
    });
    if (halteList.length === 0) {
        $('#halte-list .help').show();
    }
}

function writeHaltesWithoutLine() {
    $('#halte-list span').remove();
    var haltes = [];
    $.each(halteList, function(i, stop) {
        halte_id = stop[0];
        if ($.inArray(halte_id, haltes) === -1) {
            haltes.push(halte_id);
        }
    });
    $.each(haltes, function(i, halte) {
        $('#halte-list').append('<span class="stop-selection pull-left label label-primary" id="s'+halte+'">'+halte+delLink+'</span');
    });
    if (halteList.length === 0) {
        $('#halte-list .help').show();
    }
}

function stopDict(stop, line) {  // DONE: adapted to lines per stop
    var selectedLinesOfStop = [];
    // check if current active line has dictionary
    if (lineSelectionOfStop.hasOwnProperty(stop)) {
        selectedLinesOfStop = selectedLinesOfStop[stop];
        // check if current selected stop is already included
        if ($.inArray(line, selectedLinesOfStop) === -1) {
                selectedLinesOfStop.push(line);
                lineSelectionOfStop[stop] = selectedLinesOfStop;
        }
    } else { /* create dict of stop and add current line to new list */
        selectedLinesOfStop.push(line);
        lineSelectionOfStop[stop] = selectedLinesOfStop;
    }
}

function removeStopFromDict(id, line){  // TODO: change to current dict-form
    // linenr already implemented in 'id'
    if (id != 'all') {
        var stop = id.split('-')[0];
        var selection = lineSelectionOfStop[stop];
        var index = selection.indexOf(line);
        if (index !== -1){
            selection.splice(index,1);
            if (selection.length == 0) {
                delete lineSelectionOfStop[stop];
            } else {
                lineSelectionOfStop[stop] = selection;
            }
        }
    } else {
        stops = Object.keys(lineSelectionOfStop);
        $.each(stops, function(i,stop) {
            id = $.inArray(line, lineSelectionOfStop[stop]);
            if (id !== -1) {
                lineSelectionOfStop[stop].splice(id, 1);
            }
            if (lineSelectionOfStop[stop].length == 0) {
                delete lineSelectionOfStop[stop];
            }
        })
    }
}

function writeLineOutputAsString(data) {  // DONE: adapted to lines per stop
    var out = "";
    $.each(data, function (i, line) {
        out += line;
        out += ",";
    });
    $("#lines").val(out);
}



/* TIME FUNCTIONS */
function checkMessageTime(event, ui) {
    var starttime = parseDate($("#id_messagestarttime").val());
    var endtime   = parseDate($("#id_messageendtime").val());

    if (starttime >= endtime) {
        if ($(this).attr('id') == "id_messagestarttime") {
            endtime.setDate(endtime.getDate()+1);
            $("#id_messageendtime").val(formatDate(endtime));
        } else {
            starttime.setDate(endtime.getDate()-1);
            $("#id_messagestarttime").val(formatDate(starttime));
        }
    }
}

function calculateTime(event, ui) {
    var text = $(this).val().replace(':', '');
    var change = false;
    var newdate = new Date(); /* Note, set date to the client date... */
    if (text.length <= 2) {
        change = true;
        newdate.setHours(parseInt(text), 0, 0);

    } else if (text.length == 3) {
        change = true;
        newdate.setHours(parseInt(text.slice(0,1)),
                         parseInt(text.slice(1,3)), 0);

    } else if (text.length == 5) {
        change = true;
        newdate.setHours(parseInt(text.slice(0,1)),
                         parseInt(text.slice(1,3)),
                         parseInt(text.slice(3,5)));

    } else if (text.length == 4) {
        change = true;
        newdate.setHours(parseInt(text.slice(0,2)),
                         parseInt(text.slice(2,4)), 0);

    } else if (text.length == 6) {
        change = true;
        newdate.setHours(parseInt(text.slice(0,2)),
                         parseInt(text.slice(2,4)),
                         parseInt(text.slice(4,6)));
    }
    if (change) {
        if (newdate < new Date()) {
            newdate.setDate(newdate.getDate()+1);
        }
        $(this).val(formatDate(newdate))
    }
}

function formatDate(d) {
    out = d.getDate() + "-" + (d.getMonth()+1) + "-" + d.getFullYear();
    out += " "+padTime(d.getHours())+":"+padTime(d.getMinutes())+":"+padTime(d.getSeconds());
    return out
}

function parseDate(d) {
    var parts = d.split(' ');
    var dateparts = parts[0].split('-');
    var timeparts = parts[1].split(':');

    // Workaround because Date.parse will get into timezone issues.
    var newdate = new Date();
    newdate.setFullYear(dateparts[2]);
    newdate.setMonth(dateparts[1]-1);
    newdate.setDate(dateparts[0]);
    newdate.setHours(timeparts[0],timeparts[1],timeparts[2]);

    return newdate;
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

function hideEndTime() {
    $('#div_id_messageendtime').hide();
    $('#id_messageendtime').val('31-12-2099 00:00:00');
}

function showEndTime() {
   $('#div_id_messageendtime').show();
   var enddate = new Date();
   enddate.setHours(3, 0, 0);
   enddate.setDate(enddate.getDate()+1);
   $('#id_messageendtime').val(formatDate(enddate));

}