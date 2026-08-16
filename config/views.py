from django.shortcuts import render


def csrf_failure(request, reason=""):
    return render(request, "403.html", status=403)


def preview_error_page(request, template_name):
    return render(request, template_name)
