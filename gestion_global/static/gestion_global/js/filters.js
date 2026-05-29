(function () {
    var forms = document.querySelectorAll('[data-gg-autofilter]');
    if (!forms.length) {
        return;
    }

    document.documentElement.classList.add('gg-js-ready');

    forms.forEach(function (form) {
        var search = form.querySelector('input[type="search"]');
        var selects = form.querySelectorAll('select');
        var inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="search"])');
        var timer = null;
        var controller = null;

        function getTableCard() {
            return document.querySelector('.gg-table-card');
        }

        function buildUrl() {
            var data = new FormData(form);
            var params = new URLSearchParams();
            data.forEach(function (value, key) {
                value = String(value || '').trim();
                if (value) {
                    params.set(key, value);
                }
            });
            return form.action.split('?')[0] + (params.toString() ? '?' + params.toString() : '');
        }

        function replaceTableFrom(html) {
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, 'text/html');
            var nextCard = doc.querySelector('.gg-table-card');
            var currentCard = getTableCard();

            if (!nextCard || !currentCard) {
                window.location.href = buildUrl();
                return;
            }

            currentCard.replaceWith(nextCard);
            nextCard.classList.add('is-updated');
            window.setTimeout(function () {
                nextCard.classList.remove('is-updated');
            }, 260);
        }

        function submitFilter() {
            if (!window.fetch || !window.DOMParser || !window.history) {
                form.requestSubmit ? form.requestSubmit() : form.submit();
                return;
            }

            var url = buildUrl();
            var card = getTableCard();
            if (controller) {
                controller.abort();
            }
            controller = new AbortController();

            if (card) {
                card.classList.add('is-loading');
            }

            fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                signal: controller.signal
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('HTTP ' + response.status);
                    }
                    return response.text();
                })
                .then(function (html) {
                    replaceTableFrom(html);
                    window.history.replaceState({}, '', url);
                })
                .catch(function (error) {
                    if (error.name !== 'AbortError') {
                        form.requestSubmit ? form.requestSubmit() : form.submit();
                    }
                })
                .finally(function () {
                    var freshCard = getTableCard();
                    if (freshCard) {
                        freshCard.classList.remove('is-loading');
                    }
                });
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

        inputs.forEach(function (input) {
            var eventName = input.type === 'date' || input.type === 'checkbox' || input.type === 'radio' ? 'change' : 'input';
            input.addEventListener(eventName, submitSoon);
        });
    });
})();
