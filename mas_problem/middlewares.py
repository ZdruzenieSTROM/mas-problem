from competition.models import UTMinfo


class UTMMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        source=request.GET.get('utm_source')        
        medium=request.GET.get('utm_medium')
        campaign=request.GET.get('utm_campaign')
        content=request.GET.get('utm_content')
        if source or medium or campaign or content:
            UTMinfo.objects.create(
                source=source,
                medium=medium,
                campaign=campaign,
                content=content,
            )
        response = self.get_response(request)
        return response
    
