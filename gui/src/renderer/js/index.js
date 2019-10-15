GUIBIND("#expcfg");
zoom_helper_enable = "svg_container";

//load or save the table
//table system
TABLEBIND("eta_index_table");

d3.select('#exp_name').on('change.2', function () {
    d3.select('#exp_tilte').text(d3.select('#exp_name').property("value"));
})
d3.select('#exp_name').on('change.2')();
// button click
d3.select('#btn_save_exp').on('click', function () {
    var obj = export_localstorage();
    var expname = d3.select('#exp_name').property("value");
    d3.select('#exp_name').classed("is-invalid", (expname.length <= 0));
    if (expname.length > 0)
        save_file(expname + ".eta", JSON.stringify(obj));
    else
        d3.select('#btn_settings').on('click')();
});


d3.select('#btn_load_exp').on('click', function () {

    // Invoked when a file is selected in dialog
    function on_file_selected() {
        var f = this.files[0];
        var reader = new FileReader();
        reader.onload = function () {
            // Invoked when a file is loaded

            on_file_loaded(f.name, JSON.parse(this.result));
        };
        reader.readAsText(f);
    }

    var input = d3.select('body').append('input')
        .attr('type', 'file')
        .style('opacity', '0')
        .on('change', on_file_selected)
        .each(function () {
            this.click();
        })
        .remove();
});

// hot-key bindings
d3.select('body').on('keydown', function () {
    if (d3.event.type === 'keydown') {
        var evObj = document.createEvent('Events');
        evObj.initEvent("click", true, false);
        switch (d3.event.keyCode) {
            case 83: //S
                if (d3.event.ctrlKey) {
                    document.getElementById('btn_save_exp').dispatchEvent(evObj);
                    d3.event.stopPropagation();
                    d3.event.preventDefault();
                }
                break;
            case 79: //O
                if (d3.event.ctrlKey) {
                    document.getElementById('btn_load_exp').dispatchEvent(evObj);
                    d3.event.stopPropagation();
                    d3.event.preventDefault();
                }
                break;
            case 13: //Enter
                if (d3.event.shiftKey || d3.event.ctrlKey) {
                    document.getElementById('btn_compile').dispatchEvent(evObj);
                    d3.event.stopPropagation();
                    d3.event.preventDefault();
                }
                break;
            default:
                console.log("Key down", d3.event.keyCode)
                break;
        }
    }
});




//TABLE EXTENSION

$('.table-design').click(function () {
    var $row = $(this).parents('tr');
    var $td = $row.find('td');
    window.open("./design.html?edit=" + $td.eq(0).text() + "&name=" + $td.eq(1).text())
});
$('.table-dpp').click(function () {
    var $row = $(this).parents('tr');
    var $td = $row.find('td');
    window.open("./processing.html?edit=" + $td.eq(0).text() + "&name=" + $td.eq(1).text())
});
$('.table-run').click(function () {
    var $row = $(this).parents('tr');
    var $td = $row.find('td');
    process_eta($td.eq(0).text(), $td.eq(2).text());
});
$('.table-openfile').click(function () {
    var $td = $(this).parents('tr').find('td');

    recipe_set_filename($td.eq(0).text(), $td.eq(1).text())
});
// Tooltip and buttons
d3.select('#btn_backend').on('click', function () {
    window.open("./processing.html");
});

$('#add-ri').click(function () {
    $("#riModal").modal({ backdrop: 'static', keyboard: false });
});
$('#add-vi').click(function () {
    create_item("vi_template")
});
$('#add-var').click(function () {
    create_item("var_template", "NewParameter", "main", "", "value")
});
$('#add-dpp').click(function () {
    create_item("dpp_template", "NewPanel")
});
function ri_table(form) {
    form.addEventListener('submit', function (event) {
        if (form.checkValidity() === false) {
            form.classList.add('was-validated');
        } else {
            form.classList.remove('was-validated');
            codegen = `[${$('#ri2').val()},${$('#ri3').val()}]`;
            $("#riModal").modal('hide');
            create_item("ri_template", $('#ri1').val(), "main","", codegen);
        }
        event.preventDefault();
        event.stopPropagation();
    }, false);
}
ri_table(document.getElementById('ri_table'))

d3.select('#btn_settings').on('click', function () {
    $("#connectModal").modal({ backdrop: 'static', keyboard: false });
});

// new dialog

$('#btn_new_exp').on('click', function () {
    $("#create_new_Modal").modal({ backdrop: 'static', keyboard: false });
});

document.querySelector("#create_new_form").addEventListener("submit", function (event) {
    $("#create_new_Modal").modal('hide');
    var data = new FormData(document.querySelector("#create_new_form"));
    for (const entry of data) {
        $.getJSON('./js/recipes/' + entry[1] + ".eta", function (data) {
            on_file_loaded(entry[1], data);
        });

    };
    event.preventDefault();
    event.stopPropagation();
}, false);

// websocket
ws = null;

d3.select('#btn_connect').on('click', function () {
    if (ws != null) {
        ws.close();
        d3.select('#ws').classed("is-valid", false);
        d3.select('#ws').classed("is-invalid", false);
        ws = null;
    }
    if (d3.select('#btn_connect').text() == "Disconnect") {
        return;
    }
    try {
        ws = new ReconnectingWebSocket(d3.select('#ws').property("value"))
    } catch (error) {
        d3.select('#ws').classed("is-valid", false);
        d3.select('#ws').classed("is-invalid", true);
        return;
    }

    ws.onopen = function (t) {
        d3.select('#btn_connect').text("Disconnect");
        d3.select('#ws').classed("is-valid", true);
        d3.select('#ws').classed("is-invalid", false);
        //Hide the modal
        $("#connectModal").modal('hide');
    }
    ws.onerror = function (t) {
        d3.select('#ws').classed("is-valid", false);
        d3.select('#ws').classed("is-invalid", true);
        if ($('#remoteModal').hasClass('show'))
        {
            ws.onmessage({'data':JSON.stringify(['err','Lost connection to Backend, retrying... <br/>You may need to restart the backend.'])});
        }
    };
    ws.onclose = function (t) {
        d3.select('#btn_connect').text("Connect");
    };

    ws.onmessage = function (t) {
        var ret = JSON.parse(t.data);
        if (ret[0] == "err") {
            ret[1] = "⚠" + ret[1];
            $("#exampleModalClose").toggleClass("d-none", false); //allow closing on error
            $("#exampleModalLabel").html('🛑 ETA Error');
        }
        if (ret[0] == "log" || ret[0] == "err") {
            $("#remoteModal").modal();
            $("#remoteLOG").html($("#remoteLOG").html() + "<br/>" + ret[1]);
        }
        if (ret[0] == "table") {
            load_table(ret[1]);
            update_to_ls();
        }
        if (ret[0] == "running") {
            $("#exampleModalClose").toggleClass("d-none", true);
            $("#exampleModalLabel").html('<div class="loader d-inline-block"></div> <div class="d-inline-block">ETA Running...</div>');
            $("#btn_viewresult").toggleClass("d-none", true);
            $("#remoteLOG").html($("#remoteLOG").html() + "<br/>" + ret[1]);
        }
        if (ret[0] == "stopped") {
            $("#exampleModalClose").toggleClass("d-none", false);
            $("#exampleModalLabel").html('<img src="favicon.ico" style="width: 2em;"/> ETA Results');
            $("#remoteLOG").html($("#remoteLOG").html() + "<br/>" + ret[1]);
        }
        if (ret[0] == "clear") {
            $("#remoteLOG").html("");// clear log
        }
        if (ret[0] == "dash") {
            $("#exampleModalClose").toggleClass("d-none", false);
            $("#btn_viewresult").toggleClass("d-none", false);
            $("#btn_viewresult").unbind("click");
            $("#btn_viewresult").click(function (d) {
                    window.open(ret[1]);
            });

            $("#btn_discardresult").toggleClass("d-none", false);
            $("#btn_discardresult").unbind("click");
            $("#btn_discardresult").click(function (d) {
                    $.ajax({
                        url: ret[1] + "/shutdown",
                        context: document.body
                    });
            });
        }
        if (ret[0] == "discard") {
            $("#exampleModalClose").toggleClass("d-none", false);
            $("#remoteModal").modal('hide');
            $("#exampleModalLabel").html('ETA Backend');
            $("#btn_viewresult").toggleClass("d-none", true);
            $("#btn_discardresult").toggleClass("d-none", true);
            $("#btn_viewresult").unbind("click");
            $("#btn_discardresult").unbind("click");
            $("#remoteLOG").html("");// clear log
        }
    }

});


function check_connectivity() {
    if (d3.select('#btn_connect').text() != "Connect") {
        return true;
    }
    d3.select('#btn_settings').on('click')();
    if (ws == null) {
        console.log("Backend is connecting...");
        d3.select('#btn_connect').on('click')();
    }

    return false;
}
d3.select('#btn_connect').on('click')();


//RPC calls

// vi checking
d3.select('#btn_compile').on('click', function () {
    if (check_connectivity()) {
        eta_linker_result = export_localstorage();
        if (eta_linker_result) {
            var rpcobj = { 'method': "compile_eta", 'args': [eta_linker_result] };
            ws.send(JSON.stringify(rpcobj));
        }
    }
});

// run
function process_eta(id, group) {
    if (check_connectivity()) {
        eta_linker_result = export_localstorage();
        if (eta_linker_result) {
            var rpcobj = { 'method': "process_eta", 'args': [eta_linker_result, id, group] };
            ws.send(JSON.stringify(rpcobj));
        }
    }
}


// recipe_set_filename
function recipe_set_filename(id, key) {
    if (check_connectivity()) {
        eta_linker_result = export_localstorage();
        if (eta_linker_result) {
            var rpcobj = { 'method': "recipe_set_filename", 'args': [eta_linker_result, id, key] };
            ws.send(JSON.stringify(rpcobj));
        }
    }
}
