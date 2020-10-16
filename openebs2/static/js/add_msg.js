/* STOP AND SCENARIO FUNCTIONS */
var selectedStops = []
var scenarioStops = []
var blockedStops = [] /* Already have messages set */
var currentLine = null
var lineSelectionOfStop = {}
var lineSelection = []
var line_related = document.getElementById('lijngebonden').checked;
var messageData = [] /* all info from blocked stops */
var activeLine = null /* lineplanningnumber */
var stop_searching = false;

function changeSearch(event) {
    if ($("#line_search").val().length > 0) {
        $.ajax('/line/'+$("#line_search").val(), {
            success : writeList
        });
    } else {
        $('#rows tr td.help').removeClass('hidden');
        $('#rows .line').remove();
    }
}

function searchSelection(item) {
    if (item.attr('id') === "stop_button") {
        if (stop_searching === true) return;

        $("#haltes-original").addClass('hidden');
        $("#haltes-new").removeClass('hidden');
        $("#lijngebonden").prop("checked", false).prop("disabled", true);
        $("#label_lijngebonden").css("color", "gray");
        line_related = document.getElementById('lijngebonden').checked;
        resetSelection("stop");
        stop_searching = true;
        getHaltesWithMessages();
    } else {
        $("#haltes-original").removeClass('hidden');
        $("#haltes-new").addClass('hidden');
        $("#lijngebonden").prop("checked", true).prop("disabled", false);
        $("#label_lijngebonden").css("color", "#333");
        line_related = document.getElementById('lijngebonden').checked;
        if (item.attr('id') === "line_button") {
            resetSelection("line");
        } else {
            resetSelection("stopline");
        }
        stop_searching = false;
    }
}

function stopSearch(event) {
    if ($("#halte_search").val().length > 0) {
        var term = $("#halte_search").val();
        var check = term.indexOf(' ');
        if (check > -1 ) {
           term = term.split(" ").join("_"); // weird method, but 'spaces' are apparently not working for the ajax
        }
        $.ajax('/stop/'+term, {
            success : writeStopListMiddle
        });
    } else {
        $('#stops-new .help').removeClass('hidden');
        $('.specificeer-middle').addClass('hidden');
        $('.stop').remove();
    }
    if ($("#haltelijn_search").val().length > 0) {
        var term = $("#haltelijn_search").val();
        var check = term.indexOf(' ');
        if (check > -1 ) {
           term = term.split(" ").join("_"); // weird method, but 'spaces' are apparently not working for the ajax
        }
        $.ajax('/stop/'+term, {
            success : writeStopList
        });
    } else {
        $('#stop_rows .help, #rows2 td.help').removeClass('hidden');
        $('.specificeer, #reset').addClass('hidden');
        $('.search_stop, #rows2 .line').remove();
    }
}

function changeCount(event) {
    len = $(this).val().length;
    addon = $(this).parents('.countwrapper').find('.charcount')[0];
    $(addon).text(len);
    $(addon).removeClass('badge-success badge-warning badge-danger');
    if (len < 178) {
       $(addon).addClass('badge-success');
    } else if (len > 177 && len < 250) {
       $(addon).addClass('badge-warning');
    } else if (len > 249) {
       $(addon).addClass('badge-danger');
    }
}

function writeList(data, status, item) {
    validIds = [];
    $('#rows2 td.help').addClass('hidden');

    /* Add them all, as neccesary */
    $.each(data.object_list, function (i, line) {
        validIds.push('l'+line.pk);
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
                if (item == 1){
                    $(row).hide().appendTo('#rows2').fadeIn(999);
                } else {
                    $(row).hide().appendTo('#rows').fadeIn(999);
                }
            }
        }
    });

    /* Cleanup */
    if (item == 1){
        $('#rows2 tr td.help').addClass('hidden');
        $("#rows2 .line").each(function(index) {
            if ($.inArray($(this).attr('id'), validIds) == -1) {
                $(this).fadeOut(999).remove();
            }
        });
    } else {
        $('#rows tr td.help').addClass('hidden');
        $("#rows .line").each(function(index) {
            if ($.inArray($(this).attr('id'), validIds) == -1) {
                $(this).fadeOut(999).remove();
            }
        });
    }
}

function showStopsOnChange() {
    $('.stopRow span').remove();
    if (!activeLine) return;
    var line = null;
    if (line_related) {
        line = activeLine;
    }
    blockedStops = [];
    if (messageData.length > 0) {
        const filtered = messageData.filter(message => {
            if (message.line == line) {
                start_epoch = epoch(parseDate($('#id_messagestarttime').val()));
                end_epoch = epoch(parseDate($('#id_messageendtime').val()));
                if (message.starttime <= start_epoch && message.endtime >= start_epoch) {
                    return true
                }
            }
        });
        var stops = [];
        if (filtered.length > 0) {
            filtered.filter(message => {
                if ($.inArray(message.userstopcode, stops) == -1) {
                    stops.push(message.userstopcode);
                }
            });
            $.each(stops, function(i, stop) {
                if (line_related){
                    $('[id*='+stop+']').append('<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een bericht voor deze lijn en begintijd"></span>');
                } else {
                    $('[id*='+stop+']').append('<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een lijnonafhankelijk bericht voor deze begintijd"></span>');
                }
                blockedStops.push(stop);
            });
        }
    }
    filterCurrentHalteList();
    $('.stopRow td.success').append('<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;');
}


function showStops(event) {
    $("#rows tr.success").removeClass('success');
    $(".suc-icon").remove();
    $(event.currentTarget).children('td').eq(1).append('<span class="suc-icon pull-right glyphicon glyphicon-arrow-right"></span>');
    $.ajax('/line/'+$(event.currentTarget).attr('id').substring(1)+'/stops', {
        success : writeLine
    })
    $(event.currentTarget).addClass('success');
}

function selectStop(event, ui) {
    $('#halte-list .help').addClass('hidden');

    if ($(ui.selected).attr('id').startsWith('sl')) {
        var stop_id = $(ui.selected).attr('id').split("_")[1];
    } else {
        var stop_id = $(ui.selected).attr('id').split("_")[1].slice(0,-1);
    }
    if ($.inArray(stop_id, blockedStops) != -1 & $('#id_messagetype_3').parent().hasClass('active') === false) { // if blocked and no OVERRULE
        return
    }
    if (doSelectStop(ui.selected)) {
        writeHaltesField();
    }
}

function selectStopFromBall(obj) {
    $('#halte-list .help').addClass('hidden');

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

function selectAllVisibleStops() {
    $('#halte-list .help').addClass('hidden');
    $('#stops .stop').each(function(index, value) {
        /* Check this is not already selected */
        index = $(this).attr('id').slice(0, -1);
        var selected = selectedStops.filter(stop => stop[2] === index && stop[1] === currentLine);
        if (selected.length == 0) {
            doSelectStop($(this));
        }
    });
    writeHaltesField();
}

function deselectAllVisibleStops() {
    var line = currentLine;
    var id = $.inArray(line, lineSelection);
    lineSelection.splice(id, 1);
    removeStop('all', line);
    writeHaltesField();
}

function doSelectStop(obj) {
    /* Make sure to strip the 'l' or 'r' */
    if (obj.id.startsWith('sl')) {
        var id = $(obj).attr('id').substring(2);
    } else {
        var id = $(obj).attr('id').slice(0, -1);
    }
    var selectedLines = [];
    if (lineSelectionOfStop[id] !== undefined) {
            selectedLines = lineSelectionOfStop[id];
    }
    var index = $.inArray(currentLine, selectedLines);
    if (index == -1) {
        if (obj.id.startsWith('sl')) {
            $('#sl'+id).addClass('success');
            $('#sl'+id).append('<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;');
            var headsign = obj.textContent;
        } else {
            $("#"+id+"l, #"+id+"r").addClass('success');
            $("#"+id+"l, #"+id+"r").append('<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;');
            if ($(obj).hasClass('stop-left')) {
                direction = "heen";
            } else if ($(obj).hasClass('stop-right')) {
                direction = "trg";
            }
            var headsign = $(obj).text()+'('+direction+') ';
        }
        selectedStops.push([headsign, currentLine, id]);
        selectedLines.push(currentLine);
        lineSelectionOfStop[id] = selectedLines;
        var i = $.inArray(currentLine, lineSelection);
        if (i == -1) {
            lineSelection.push(currentLine);
        }
        // check if other selected lines have this stop also
        searchSelectedLinesForStop(id.substring(1));
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
    }
    $.each(selectedStops, function(i, stop) {
        if (stop !== undefined) {
            if (lijngebonden.hasAttribute("disabled") === true) {
                var stop_id = stop[2];
            } else {
                var stop_id = stop[2].substring(1);
            }
            if ($.inArray(stop_id, stops) === -1) {
                stops.push(stop_id);
            }
        }
    });
    $.each(stops, function(index, halte) {
        out += halte+",";
    });
    $("#haltes").val(out);

    if (line_related) {
        writeHaltesWithLine();
    } else {
        writeHaltesWithoutLine();
    }
}

/* Do the inverse in case we're editing or something */
function readHaltesField() {
    if (window.location.pathname.split('/')[1] === 'bericht') {
        message_nr = window.location.pathname.split('/')[2];
        if (message_nr == 'nieuw') return;
        $.ajax('/bericht/'+message_nr+'/haltes', {
                success : getMyData
        });
    } else if (window.location.pathname.split('/')[1] === 'scenario') {
        scenario_nr = window.location.pathname.split('/')[2];
        message_nr = window.location.pathname.split('/')[4];
        if (message_nr === 'nieuw') return;
        $.ajax('/scenario/'+scenario_nr+'/bericht/'+message_nr+'/haltes', {
                success : getMyData
       });
    }
}

function getMyData(data){
    my_data = data;
    $.each(data.object, function (i, line) {
        var lineplanningnumber = i.split('/')[1]
        if (lineplanningnumber == "None") {
            lineplanningnumber = "Onbekend";
            line_related = false;
            lineSelection.push(lineplanningnumber);
            $('#lijngebonden').prop("checked", false);
        } else {
            line_related = true;
            lineSelection.push(lineplanningnumber);
        }
        $.each(line, function(idx, stop) {
            if ($.inArray([stop[1], lineplanningnumber, 's'+stop[0]], selectedStops) == -1) {
                selectedStops.push([stop[1], lineplanningnumber, 's'+stop[0]]);
            }
            if (lineSelectionOfStop['s'+stop[0]] === undefined) {
                lineSelectionOfStop['s'+stop[0]] = [];
            }
            lineSelectionOfStop['s'+stop[0]].push(i.split('/')[1])
        });
    });
    writeHaltesField();
}

/* Wrapper functions to get the id */
function selectionRemoveStop(event) {
    var stop_id = '';
    var line = null;
    if (line_related) {
        stop_id = $(this).parent().attr('id').split('-')[0].substring(1);
        line = $(this).parent().parent().attr('id').substring(4);
    } else {
        stop_id = $(this).parent().attr('id').substring(1);
        line = currentLine;
    }
    removeStop(stop_id, line);
}

function lineRemoveStop(event) {
    removeStop($(this).attr('id').slice(0, -1))
}

function removeStopsOfLine(event) {
    var line = $(this).parent().parent().attr('id').substring(4);
    var idx = $.inArray(line, lineSelection);
    lineSelection.splice(idx, 1);

    $.each(lineSelectionOfStop, function (stop, lines) {
        var idx = $.inArray(line, lines);
        if (idx !== -1) {
            lines.splice(idx, 1);
            lineSelectionOfStop[stop] = lines;
            if (lineSelectionOfStop[stop].length == 0) {
                delete lineSelectionOfStop[stop];
            }
        }
    });

    var new_selection = selectedStops.filter(stop => stop[1] !== line);
    selectedStops = new_selection;

    if (line === currentLine) {
        $(".stop").removeClass('success');
        $(".stop-check").remove();
    }

    var id_end = '-'+line;
    $('[id$='+id_end+']').remove();

    if (Object.keys(lineSelectionOfStop).length == 0) {
        $('#halte-list .help').removeClass('hidden');
    }
    $('#'+$(this).parent().parent().attr('id')).remove();

    writeHaltesField();
}

/* Do the actual work here */
function removeStop(id, line) {
    if (id == 'all') {
        for (var i = 0; i < selectedStops.length; i++) {
            if (selectedStops[i][1] == line) {
                if (line === currentLine) {
                    var old_id = selectedStops[i][2];
                    $("#"+old_id+"l, #"+old_id+"r").removeClass('success');
                    $("#"+old_id+"l .stop-check, #"+old_id+"r .stop-check").remove();
                    var idx = $.inArray(line, lineSelection)
                    if (idx !== -1) {
                        lineSelection.splice(idx, 1);
                    }
                }
                selectedStops.splice(i, 1);
                i--;
            }
        }
        removeStopFromDict(id, line);
    } else {
        var lijnen = [];
        var selection = selectedStops.filter(stop => stop[2] === id);
        if (selection.length > 0) {
            $.each(selection, function(i, row) {
                var idx = selectedStops.indexOf(row);
                selectedStops.splice(idx, 1);
                lijnen.push(row[1]);
                removeStopFromDict(row[2], row[1]);
            });
            var halte = id;
            if (line_related) {
                halte = id+'-'+line;
            }
            $('[id^=s'+id+']').remove();
        }

        $.each(lijnen, function(i, lijn) {
            if (lijn === currentLine) {
                var old_id = id.split('-')[0].substring(1);
                $("#"+id+"l, #"+id+"r").removeClass('success');
                $("#"+id+"l .stop-check, #"+id+"r .stop-check").remove();
            }
            var result = selectedStops.filter(stop => stop[1] === lijn);
            if (result.length === 0) {
                var j = $.inArray(lijn, lineSelection);
                lineSelection.splice(j, 1);
            }
        });
    }
    writeHaltesField()
}

function writeLine(data, status) {
    $('#stops tr.help').addClass('hidden');
    $("#haltes-original .stopRow").remove();
    var out = "";
    if (stop_searching == true) {
        $.each(data.object.stop_map, function (i, stop) {
        out = renderHaltesNew(stop);
        });
    } else {
        $.each(data.object.stop_map, function (i, stop) {
            out += renderRow(stop);
        });
    }
    $('#stops').append(out)
    $('#stops').fadeIn(200);
    $('.stop_btn').removeClass('hide');
}

function renderRow(row) {
    var stopSelection = [];
    var currentStopMeasures = [];
    if ($('#id_messagestarttime').val() !== undefined) {
        var messagestarttime = epoch(parseDate($('#id_messagestarttime').val()));
        var messageendtime = epoch(parseDate($('#id_messageendtime').val()));
        var line = null;
        if (line_related) {
            line = activeLine;
        }
        messageData.filter(measure => {
            if (measure.line == line) {
                if (measure.starttime <= messagestarttime && measure.endtime >= messagestarttime) {
                    stop = measure.dataownercode + '_' + measure.userstopcode;
                    currentStopMeasures.push([stop, measure.starttime, measure.endtime, measure.line, measure.message]);
                }
            }
        });
    }
    out = '<tr class="stopRow">';
    if (row.left != null) {
        if ($.inArray(row.left.id, scenarioStops) != -1) {
            out += '<td class="warning">'+row.left.name+' <span class="glyphicon glyphicon-warning-sign pull-right" title="Al in scenario opgenomen"></span></td>'
        } else {
            var id = 's'+row.left.id+'l';
            if (lineSelectionOfStop['s'+row.left.id] !== undefined) {
                stopSelection = lineSelectionOfStop['s'+row.left.id];
            }
            if ($.inArray(currentLine, stopSelection) != -1) {
                out += '<td class="stop stop-left success" id="'+id+'">'+row.left.name+'<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;'
            } else {
                out += '<td class="stop stop-left" id="'+id+'">'+row.left.name;
                var selected = currentStopMeasures.filter(message => message[0] === row.left.id);
                if (selected.length > 0) {
                    if (line_related) {
                        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een bericht voor deze lijn en begintijd"></span>'
                    } else {
                        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een lijnonafhankelijk bericht voor deze begintijd"></span>'
                    }
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
        stopSelection = []
        if ($.inArray(row.right.id, scenarioStops) != -1) {
            out += '<td class="warning">'+row.right.name+' <span class="glyphicon glyphicon-warning-sign pull-right" title="Al in scenario opgenomen"></span></td>'
        } else {
            var id = 's'+row.right.id+'r';
            if (lineSelectionOfStop['s'+row.right.id] !== undefined) {
                stopSelection = lineSelectionOfStop['s'+row.right.id];
            }
            if ($.inArray(currentLine, stopSelection) != -1) {
                out += '<td class="stop stop-right success" id="'+id+'">'+row.right.name+'<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;</td>';
            } else {
                out += '<td class="stop stop-right" id="'+id+'">'+row.right.name;
                var selected = currentStopMeasures.filter(message => message[0] === row.right.id);
                if (selected.length > 0) {
                    if (line_related) {
                        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een bericht voor deze lijn en begintijd"></span>'
                    } else {
                        out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een lijnonafhankelijk bericht voor deze begintijd"></span>'
                    }
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

function renderHaltesNew(stop) {  // TODO: fix this :)
    out = '<tr class="stop">';
    var id = 'sl'+stop.id;
    if (lineSelectionOfStop['sl'+stop.id] !== undefined) {
        stopSelection = lineSelectionOfStop['sl'+stop.id];
    }
    if ($.inArray(currentLine, stopSelection) != -1) {
        out += '<td class="stop stop-left success" id="'+id+'">'+stop.name+'<span class="stop-check glyphicon glyphicon-ok-circle pull-right"></span>&nbsp;'
    } else {
        out += '<td class="stop stop-left" id="'+id+'">'+stop.name;
        var selected = currentStopMeasures.filter(message => message[0] === stop.id);
        if (selected.length > 0) {
            out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een bericht voor deze begintijd"></span>'
        }
        out += '</td>';
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

function getHaltesWithMessages(event) {
    if (stop_searching == false) {
        if ($(this).attr('id') !== undefined) {
            activeLine = $(this).attr('id').substring(1);
            currentLine = $(this).find("small").text();
        }
    }
    if (document.getElementById('id_messagestarttime') !== null) {
        var starttime = parseDate($("#id_messagestarttime").val()).toJSON()

        $.ajax({ url: '/bericht/haltes.json',
                data: {'messagestarttime': starttime},
                success : function(data) {
                    writeHaltesWithMessages(data);
                    if (stop_searching == false) {
                        showStops(event);
                    } else {
                        showStopsOnChange();
                    }
                }
        });
    } else {
        showStops(event);
    }
}

function writeHaltesWithMessages(data) {
    $('.stopRow span').remove();
    blockedStops = [];
    messageData = data.object;
    if (activeLine) {
        var line = null;
        if (line_related) {
            line = activeLine
        }
        $.each(data.object, function (i, halte) {
            if (halte['line'] == line) {
                blockedStops.push(halte['userstopcode'])
            }
        });
    } else {  /* shouldn't be neccassary, but just in case */
        $.each(data.object, function (i, halte) {
            blockedStops.push(halte['userstopcode'])
        });
    }
}

function lineRelated() {
    line_related = document.getElementById('lijngebonden').checked;
    if ($("#id_messagestarttime").val() === undefined) {
        switchHaltesField();
    } else {
        var starttime = parseDate($("#id_messagestarttime").val()).toJSON()
        $.ajax({ url: '/bericht/haltes.json',
                data: {'messagestarttime': starttime},
                success : function(data) {
                    writeHaltesWithMessages(data);
                    showStopsOnChange();
                    switchHaltesField();
                }
        });
    }
}

function switchHaltesField() {
    if (line_related) {
        $('#halte-list span').remove();
    } else {
        $('#halte-list div').remove();
        $('#lines').val('');
    }
    writeHaltesField();
}

function writeHaltesWithLine() {
    $('#halte-list div').remove();
    $('#lijnfix').remove();
    $('.all_stops').remove();
    var delLine = '<span class="line-remove glyphicon glyphicon-remove"></span>';
    $.each(lineSelection, function (index, line) {
        $("#halte-list").append('<div><p class=lijn'+line+' id=lijn'+line+'><span class="stop-selection pull-left label label-danger">Lijn: '+line+ ' '+delLine+'</span></p><br /></div><div class="clearfix" id="lijnfix"></div>');
    });
    var delLink = '<span class="stop-remove glyphicon glyphicon-remove"></span>';
    $.each(selectedStops, function(i, stop) {
        var halte_id = stop[2];
        var lijn = stop[1];
        var headsign = stop[0];
        $('.lijn'+lijn).append('<span class="stop-selection pull-left label label-primary" id="s'+halte_id+'-'+lijn+'">'+headsign+delLink+'</span');
    });
    if (selectedStops.length === 0) {
        $('#halte-list .help').removeClass('hidden');
    }
}

function writeHaltesWithoutLine() {
    $('#halte-list span').remove();
    $('#halte-list div').remove();
    $('#lijnfix').remove();
    $('.all_stops').remove();
    var haltes = {};
    $.each(selectedStops, function(i, stop) {
        var halte_id = stop[2];
        var headsign = stop[0];
        if (!haltes.hasOwnProperty(halte_id)) {
            haltes[halte_id] = headsign;
        }
    });
    var delLink = '<span class="stop-remove glyphicon glyphicon-remove"></span>';
    $("#halte-list").append('<div class="all_stops"><p></p></div><div class="clearfix" id="lijnfix"></div>')
    $.each(haltes, function(halte, headsign) {
        $('#halte-list .all_stops').append('<span class="stop-selection pull-left label label-primary" id="s'+halte+'">'+headsign+delLink+'</span');
    });
    if (selectedStops.length === 0) {
        $('#halte-list .help').removeClass('hidden');
    }
}

function stopDict(stop, line) {
    var selectedLinesOfStop = [];
    if (lineSelectionOfStop.hasOwnProperty(stop)) {
        selectedLinesOfStop = selectedLinesOfStop[stop];
        if ($.inArray(line, selectedLinesOfStop) === -1) {
                selectedLinesOfStop.push(line);
                lineSelectionOfStop[stop] = selectedLinesOfStop;
        }
    } else {
        selectedLinesOfStop.push(line);
        lineSelectionOfStop[stop] = selectedLinesOfStop;
    }
}

function removeStopFromDict(id, line){
    if (id != 'all') {
        var selection = lineSelectionOfStop[id];
        var index = selection.indexOf(line);
        if (index !== -1){
            selection.splice(index,1);
            if (selection.length == 0) {
                delete lineSelectionOfStop[id];
            } else {
                lineSelectionOfStop[stop] = selection;
            }
        }
    } else {
        var stops = Object.keys(lineSelectionOfStop);
        $.each(stops, function(i,stop) {
            var idx = $.inArray(line, lineSelectionOfStop[stop]);
            if (idx !== -1) {
                lineSelectionOfStop[stop].splice(idx, 1);
            }
            if (lineSelectionOfStop[stop].length == 0) {
                delete lineSelectionOfStop[stop];
            }
        })
    }
}

function writeLineOutputAsString(data) {
    var out = "";
    data.sort();
    $.each(data, function (i, line) {
        if (line !== "Onbekend") {
            out += line;
            out += ",";
        }
    });
    $("#lines").val(out);
}

function searchSelectedLinesForStop(stop_id) {
    var out = '';
    $.each(lineSelection, function(index, lijn) {
        out += lijn+",";
    });
    $.ajax({
        url: '/stop/'+stop_id+'/lines',
        data: {lijnen : out},
        success: addLinesToStop
    });
}

function addLinesToStop(data) {
    var stop = $('.ui-selected').attr('id').slice(0,-1);
    var linesOfStop = lineSelectionOfStop[stop];
    $.each(lineSelection, function(i, line) {
        if (line === currentLine) {
            return true;
        }
        $.each(data.object_list, function(row, dict) {
            if (dict['lineplanningnumber'] === line) {
                linesOfStop.push(line)
                var relevant_stop = selectedStops.filter(row => row[2] === stop)[0];
                selectedStops.push([relevant_stop[0], line, relevant_stop[2]])
            }
        });
    });
    lineSelectionOfStop[stop] = linesOfStop;
    writeHaltesField();
}

function filterCurrentHalteList() {
    $.each(selectedStops, function(i, stop) {
        var stop_nr = stop[2].split('_')[1];
        if ($.inArray(stop_nr, blockedStops) !== -1) {
            selectedStops.splice(i, 1);
            delete lineSelectionOfStop[stop[2]];
            $('[id^='+stop[2]+']').removeClass('success');
            $('[id^='+stop[2]+'] span').remove();
        }
    });
    writeHaltesField();
}

function getLinesOfStop(event) {
    $(".lines").remove();
    $("#rows2 .line, .suc-icon").remove();
    $("#haltes-original .stopRow").remove();
    $("#stop_rows tr.success").removeClass('success');
    $(".suc-icon").remove();
    $(event.currentTarget).children('td').eq(1).append('<span class="suc-icon pull-right glyphicon glyphicon-arrow-right"></span>');
    $.ajax('/stop/'+$(event.currentTarget).attr('id').substring(2)+'/lines', {
        success : function(data, status, item) {
            writeList(data, status, 1)
        }
    });
    $(event.currentTarget).addClass('success');
    $('#reset').removeClass('hidden');
}

function writeStopList(data, status) {
    if ($("#haltelijn_search").val().length > 0 && data.object_list.length == 0) {
        $('#stop_rows tr.search_stop').remove();
        $('#stop_rows tr td.help').addClass('hidden');
        $('.specificeer em').text("Er werden geen haltes gevonden. Kies een andere zoekterm aub");
        $('#stop_rows .specificeer').removeClass('hidden');
        return
    }
    if (data.object_list.length > 0 ) {
        $('#stop_rows tr td.help').addClass('hidden');
        $('#stop_rows tr.search_stop').remove();

        /* Add them all, as neccesary */
        validIds = []
        $.each(data.object_list, function (i, stop) {
            validIds.push('sl'+stop.dataownercode+'_'+stop.userstopcode);
            if (!$('#sl'+stop.dataownercode+'_'+stop.userstopcode).length) {
                var out = '';
                var row = '';
                out += "<strong>"+stop.userstopcode+"</strong>";
                row = '<tr class="search_stop" id="sl'+stop.dataownercode+'_'+stop.userstopcode+'"><td>'+out+'</td>';
                row += '<td>'+stop.name+'</td></tr>';
                $(row).hide().appendTo("#stop_rows");
            }
        });
        $(document).ready(function() {
            if ($('#stop_rows tr').length > 11) {
                $('#stop_rows tr:lt(10)').fadeIn(999);
                $('#stop_rows .specificeer').removeClass('hidden');
                $('.specificeer em').text("Er waren meer dan 10 resulaten. Specificeer uw opdracht aub");
            } else {
                $('#stop_rows .specificeer').addClass('hidden');
                $('#stop_rows tr').fadeIn(999);
            }
        });
    }
}

function writeStopListMiddle(data, status) {
    if ($("#halte_search").val().length > 0 && data.object_list.length == 0) {
        $('.stop').remove();
        $('#stops-new .help').addClass('hidden');
        $('#stops-new .specificeer-middle em').text("Er werden geen haltes gevonden. Kies een andere zoekterm aub");
        $('#stops-new .specificeer-middle').removeClass('hidden');
        return
    }
    validIds = []
    if (data.object_list.length > 0 ) {
        $('#stops-new .help').addClass('hidden');
        $('.stop').remove();
    }
    /* Add them all, as neccesary */
    $.each(data.object_list, function (i, stop) {
        validIds.push('sl'+stop.dataownercode+'_'+stop.userstopcode)
        if (!$('#sl'+stop.dataownercode+'_'+stop.userstopcode).length) {
            var out = '';
            var row = '';
            out += ""+stop.userstopcode+" "+stop.name+"";
            if ($.inArray(stop.userstopcode, blockedStops) > -1) {
                out += '<span class="glyphicon glyphicon-warning-sign pull-right" title="Halte heeft al een bericht voor deze begintijd"></span>'
            }
            row = '<tr class="stop" id="sl'+stop.dataownercode+'_'+stop.userstopcode+'"><td>'+out+'</td></tr>';
            $(row).hide().appendTo("#stops-new");
        }
        $(document).ready(function() {
            if ($('#stops-new tr').length > 11) {
                $('#stops-new tr:lt(10)').fadeIn(999);
                $('.specificeer-middle em').text("Er waren meer dan 10 resulaten. Specificeer uw opdracht aub");
                $('.specificeer-middle').removeClass('hidden');
            } else {
                $('.specificeer-middle').addClass('hidden');
                $('#stops-new .stop').fadeIn(999);
            }
        }); //TODO: Check of deze buiten de .each-loop kan!
    });
    /* Cleanup */
    $("#stops-new .stop").each(function(index) {
        if ($.inArray($(this).attr('id'), validIds) == -1) {
            $(this).fadeOut(999).remove()
        }
    });
}

function resetSelection(call) {
    if (call == 'stop') {
        $("#line_search, #haltelijn_search").val('');
        $(".line, .search_stop").remove();
        $('#stop_rows .specificeer').addClass('hidden');
        $('#stop_rows tr td.help, #rows tr td.help, #stops tr.help').removeClass('hidden');
        $("#haltes-original .stopRow").remove();
        $('.stop_btn').addClass('hide');
    } else if (call == 'line') {
        $("#halte_search, #haltelijn_search").val('');
        $(".stop, .search_stop").remove();
        $('#stop_rows .specificeer, #stops-new .specificeer-middle').addClass('hidden');
        $('#stop_rows tr td.help, #stops-new tr.help').removeClass('hidden');
        $('#stops tr.help, #stops-new tr.help').removeClass('hidden');
        $("#haltes-original .stopRow, #haltes-new .stop").remove();
        $('.stop_btn').addClass('hide');
    } else {
        $("#halte_search, #line_search").val('');
        $(".stop, .line").remove();
        $('#stops-new .specificeer-middle').addClass('hidden');
        $('#rows tr td.help, #stops-new tr.help').removeClass('hidden');
        $('#stops tr.help, #stops-new tr.help').removeClass('hidden');
        $("#haltes-original .stopRow, #haltes-new .stop").remove();
        $('.stop_btn').addClass('hide');
    }
    $('#haltes').val('');
    $('#halte-list span').remove();
    $('#halte-list em.help').show();
    $('#lines').val('');
    selectedStops = [];
    lineSelectionOfStop = {};
    lineSelection = [];
}

function epoch(date) {
    return Date.parse(date) / 1000;
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