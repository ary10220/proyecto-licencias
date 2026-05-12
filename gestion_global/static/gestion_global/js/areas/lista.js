$(function () {
    var modalSelector = '#modalNuevoAreas';
    var $modal = $(modalSelector);
    if (!$modal.length) {
        return;
    }

    function initSelect2() {
        if (!$.fn.select2) {
            return;
        }
        $modal.find('.select2-busqueda').each(function () {
            var $field = $(this);
            if ($field.data('select2')) {
                return;
            }
            $field.select2({
                theme: 'bootstrap-5',
                dropdownParent: $modal,
                width: '100%',
                placeholder: 'Buscar y seleccionar...'
            });
        });
    }

    $modal.on('shown.bs.modal', initSelect2);

    if ($modal.attr('data-has-errors') === 'true') {
        $modal.modal('show');
    }
});
