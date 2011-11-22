# -*- coding: utf-8 -*-
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView

from zope.annotation.interfaces import IAttributeAnnotatable, IAnnotations


class respostaAltaCloud(BrowserView):
    """ News box main page view
    """
    __call__ = ViewPageTemplateFile('resposta_AltaCloud.pt')

    def __init__(self, context, request):
        """
        """
        self.context = context
        self.request = request

    def result_peticio(self):
        """
        """
        url_dades = ''
        url_dades = self.request.get('valor')
        return url_dades


class peticionsAltaCloud(BrowserView):
    """ News box main page view
    """

    def __init__(self, context, request):
        """
        """
        self.context = context
        self.request = request

    def __call__(self):
        """
        """
        carpetaResultats = self.context.portal_url.getPortalObject()['serveis']['servidors-i-xarxes']['servidors']['cloud-privat-upc']['registre']
        annotations = IAnnotations(carpetaResultats)
        #pruebas pilar
#        content_renderers = annotations.get('upc.cloudPrivat-registres',[])
#        return '\n'.join(['%s,%s,%s,%s' % (reg.values()[2],reg.values()[1],reg.values()[3],reg.values()[0]) for reg in content_renderers])
        #funciona
        content_renderers = annotations.get('upc.cloudPrivat-registres', {})
        if content_renderers.values() == []:
            return '\n'.join(["No s'ha registrat cap usuari"])
        return '\n'.join(['%s,%s,%s,%s,%s' % (reg.values()[2],reg.values()[0],reg.values()[4],reg.values()[1],reg.values()[3]) for reg in content_renderers.values()])
