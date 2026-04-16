(function () {
  function updateVisibility() {
    var selected = document.querySelector('select[name="action"]');
    var show = selected && selected.value === "create_schedule_for_next_30_days";

    document.querySelectorAll('input[name="start_date"]').forEach(function (input) {
      var label = input.closest("label") || input.parentElement;
      if (!label) return;
      label.style.display = show ? "" : "none";
      input.disabled = !show;
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    updateVisibility();

    document.querySelectorAll('select[name="action"]').forEach(function (sel) {
      sel.addEventListener("change", updateVisibility);
    });
  });
})();