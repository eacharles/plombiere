(function () {
    "use strict";

    var TRIGGER_MAP = {
        "dag-instance-graph": "dag-instance-rightclick-trigger",
        "dag-pipeline-graph": "dag-pipeline-rightclick-trigger",
        "dag-variant-graph": "dag-variant-rightclick-trigger"
    };

    function findGraphId(el) {
        while (el) {
            if (el.id && Object.prototype.hasOwnProperty.call(TRIGGER_MAP, el.id)) {
                return el.id;
            }
            el = el.parentElement;
        }
        return null;
    }

    document.addEventListener("contextmenu", function (e) {
        var graphId = findGraphId(e.target);
        if (!graphId) return;
        e.preventDefault();
        var btn = document.getElementById(TRIGGER_MAP[graphId]);
        if (btn) btn.click();
    });
}());
