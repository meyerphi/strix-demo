var assumptionsEditor;
var guaranteesEditor;
var inputsEditor;
var outputsEditor;

function bool_to_string(value) {
   if (value) { return "1"; } else { return "0"; }
}

function make_formula(str) {
    return "((" + str.split(/\r|\n/).map(s => s.trim()).filter(s => s.length > 0).join(") & (") + "))"
}

function make_propositions(str) {
    return str.split(/\r|\n/).join(",");
}

function create() {
  var cgi_url = "https://6i8inwv1n3.execute-api.eu-central-1.amazonaws.com/strix/synthesize"

  var assumptions = assumptionsEditor.getValue().trim();
  var guarantees = guaranteesEditor.getValue().trim();
  if (!guarantees) {
    $("#svg-container").text("Guarantees not specified")
    return;
  }

  formula = "";
  if (assumptions) {
    formula += make_formula(assumptions);
    formula += " -> ";
  }
  formula += make_formula(guarantees);

  cgi_url += "?formula=" + encodeURIComponent(formula.trim());

  var inputs = inputsEditor.getValue().trim();
  var outputs = outputsEditor.getValue().trim();
  if (!inputs && !outputs) {
    $("#svg-container").text("No input or output symbols specified")
    return;
  }
  inputs = make_propositions(inputs);
  outputs = make_propositions(outputs);
  cgi_url += "&inputs=" + encodeURIComponent(inputs);
  cgi_url += "&outputs=" + encodeURIComponent(outputs);

  var format = $("#input input[name=format]:checked").val();
  if (!format) {
    format = "mealy";
  }

  cgi_url += "&format=" + encodeURIComponent(format);
  cgi_url += "&minimize=" + bool_to_string($("#input input[name=minimize]").is(":checked"));
  cgi_url += "&labels=" + bool_to_string($("#input input[name=labels]").is(":checked"));

  // Clear, then query new
  $("#svg-container").text("Synthesizing controller - please wait a few moments");
  $("#svg-container").load(cgi_url, function(response, status, xhr) {
    if (status == "error") {
      $("#svg-container").text(response)
    }
    else {
      var imageWidth = $("#svg-container > svg").width();
      var outerWidth = $("#svg-container").width();
      $("#svg-container").scrollLeft((imageWidth - outerWidth) / 2);
    }
  });
}

function selectExample(example) {
    let path = 'examples/' + example + ".json";
    $.getJSON(path)
    .done(function(json) {
      inputsEditor.setValue(json.inputs.join(", "));
      outputsEditor.setValue(json.outputs.join(", "));
      assumptionsEditor.setValue(json.assumptions.join("\n"));
      guaranteesEditor.setValue(json.guarantees.join("\n"));
    })
    .fail(function(jqxhr, textStatus, error) {
      $("#svg-container").text("Error: cannot load example \"" + example +"\": " + error);
    });
}

function init() {
    // init editor
    let initEditor = function(id) {
        return CodeMirror.fromTextArea(document.getElementById(id), {
          lineNumbers: true,
          lineWrapping: true,
          mode: "ltl",
          theme: "3024-day",
          matchBrackets: true,
          autoCloseBrackets: true,
          extraKeys: { "Tab": false, "Shift-Tab": false }
        });
    };
    let initLineEditor = function(id) {
        return CodeMirror.fromTextArea(document.getElementById(id), {
          mode: "ltl",
          theme: "3024-day",
          lineWrapping: true,
          extraKeys: { "Tab": false, "Shift-Tab": false }
        });
    };
    assumptionsEditor = initEditor("assumptions_textarea");
    guaranteesEditor = initEditor("guarantees_textarea");
    inputsEditor = initLineEditor("inputs_textarea");
    outputsEditor = initLineEditor("outputs_textarea");

    // init examples
    $("#exampleContainer")
    .on("select_node.jstree", function(node, selected) {
      if (selected.node.children.length == 0) {
        selectExample(selected.node.id);
      }
      else {
        $("#exampleContainer").jstree(true).toggle_node(selected.node);
      }
    })
    .jstree({
      "plugins" : ["types"],
      "types" : {
        "root" : {
          "a_attr" : { "style": "font-weight: bold" },
          "li_attr" : { "style": "margin-left: 0px" },
          "icon": "jstree-icon jstree-folder"
        },
        "top-folder" : {
          "icon": "jstree-icon jstree-folder",
          "li_attr" : { "style": "margin-left: 0px" }
        },
        "folder" : {
          "icon": "jstree-icon jstree-folder"
        },
        "default" : {
          "icon": "jstree-icon jstree-file"
        }
      },
      "core" : {
        "themes": {
          "name": "default",
          "responsive": true
        },
        "data" : {
          "url": "examples/examples.json",
          "dataType" : "json"
        }
      }
    })
    .on('ready.jstree', function(){
      // remove icon next to root
      $("#examples").find("i.jstree-icon").first().removeClass("jstree-icon");
      $("#examples_anchor").find("i.jstree-icon").first().removeClass("jstree-icon");
    });
}
