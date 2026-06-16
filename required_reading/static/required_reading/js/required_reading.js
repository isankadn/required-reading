(function () {
  function confirmDeletes() {
    var forms = document.querySelectorAll('.rr-delete-form');
    forms.forEach(function (form) {
      form.addEventListener('submit', function (event) {
        var message = form.getAttribute('data-confirm') || 'Delete this document?';
        if (!window.confirm(message)) {
          event.preventDefault();
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', confirmDeletes);
  } else {
    confirmDeletes();
  }
})();
