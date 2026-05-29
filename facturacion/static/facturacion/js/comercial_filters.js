(function () {
    document.querySelectorAll('[data-commercial-filter-form]').forEach(function (form) {
        var tenantSelect = form.querySelector('select[name="tenant"], select[data-tenant-router]');
        var empresaSelect = form.querySelector('select[name="empresa"]');
        var empleadoSelect = form.querySelector('select[name="empleado"]');
        if (!tenantSelect || !empresaSelect) {
            return;
        }

        function currentTenantId() {
            var selectedOption = tenantSelect.options[tenantSelect.selectedIndex];
            return selectedOption ? (selectedOption.getAttribute('data-tenant-id') || tenantSelect.value) : tenantSelect.value;
        }

        function syncEmpresas() {
            var tenantId = currentTenantId();
            var selectedIsVisible = true;

            Array.prototype.forEach.call(empresaSelect.options, function (option) {
                if (!option.value) {
                    option.hidden = false;
                    return;
                }
                var visible = !tenantId || option.getAttribute('data-tenant') === tenantId;
                option.hidden = !visible;
                if (option.selected && !visible) {
                    selectedIsVisible = false;
                }
            });

            if (!selectedIsVisible) {
                empresaSelect.value = '';
            }
        }

        function syncEmpleados() {
            if (!empleadoSelect) {
                return;
            }

            var tenantId = currentTenantId();
            var empresaId = empresaSelect.value;
            var selectedIsVisible = true;

            Array.prototype.forEach.call(empleadoSelect.options, function (option) {
                if (!option.value) {
                    option.hidden = false;
                    return;
                }

                var optionEmpresa = option.getAttribute('data-empresa');
                var optionTenant = option.getAttribute('data-tenant');
                var visible = (!tenantId || optionTenant === tenantId) && (!empresaId || optionEmpresa === empresaId);
                option.hidden = !visible;
                if (option.selected && !visible) {
                    selectedIsVisible = false;
                }
            });

            if (!selectedIsVisible) {
                empleadoSelect.value = '';
            }
        }

        tenantSelect.addEventListener('change', function () {
            syncEmpresas();
            syncEmpleados();
        });
        empresaSelect.addEventListener('change', syncEmpleados);
        syncEmpresas();
        syncEmpleados();
    });
})();
