from .base import *  # noqa: F401,F403


class ForcedPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("home")

    def _is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get(self, request, *args, **kwargs):
        if self._is_ajax():
            form = self.get_form()
            html = render_to_string('registration/_password_change_form_inner.html', {'form': form}, request=request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        if self._is_ajax():
            html = render_to_string('registration/_password_change_form_inner.html', {'form': form}, request=self.request)
            return HttpResponse(html, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        perfil, _ = PerfilUsuario.objects.get_or_create(user=self.request.user)
        if perfil.must_change_password:
            perfil.must_change_password = False
            perfil.save(update_fields=['must_change_password'])
            log_password_change_inicial(self.request, self.request.user.username)
        if self._is_ajax():
            return JsonResponse({'ok': True})
        messages.success(self.request, "Contrasena actualizada correctamente.")
        return response
