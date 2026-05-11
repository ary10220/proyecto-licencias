(function () {
    var forms = document.querySelectorAll('[data-gg-autofilter]');
    if (!forms.length) {
        return;
    }

    document.documentElement.classList.add('gg-js-ready');

    forms.forEach(function (form) {
        var search = form.querySelector('input[type="search"]');
        var selects = form.querySelectorAll('select');
        var timer = null;

        function submitFilter() {
            form.requestSubmit ? form.requestSubmit() : form.submit();
        }

        function submitSoon() {
            window.clearTimeout(timer);
            timer = window.setTimeout(submitFilter, 450);
        }

        if (search) {
            search.addEventListener('input', submitSoon);
            search.addEventListener('keydown', function (event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    window.clearTimeout(timer);
                    submitFilter();
                }
            });
        }

        selects.forEach(function (select) {
            select.addEventListener('change', submitFilter);
        });
    });
})();
