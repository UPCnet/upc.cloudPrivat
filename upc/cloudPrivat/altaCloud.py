# -*- coding: utf-8 -*-

from zope import interface, schema
from z3c.form import form, field, button
from plone.z3cform.layout import wrap_form

from zope.schema.fieldproperty import FieldProperty
import zope.interface

from Products.CMFCore.utils import getToolByName

from zope.interface import invariant
from zope.interface import Invalid


from upc.cloudPrivat import altaCloudMessageFactory as _

import urllib2

from zope.annotation.interfaces import IAttributeAnnotatable, IAnnotations
import datetime

from zope.app.pagetemplate import viewpagetemplatefile
from plone.z3cform import layout
import re


class OverridableTemplate(object):
    """Subclasses of this class must set the template they want to use
    as the default template as the ``index`` attribute, not the
    ``template`` attribute that's normally used for forms.

    Users of this package may override the template used by one of the
    forms by using the ``browser`` directive and specifying their own
    template.
    """
    @property
    def template(self):
        return self.index


#Interface on creem els camps del formulari
class IAltaCloud(interface.Interface):
    nom_usuari = schema.TextLine(title=u"Nom d'usuari", description=u"El nom d'usuari d'accés al Cloud Privat UPC serà el mateix que el nom d'usuari de la intranet UPC", readonly=True, required=True)
    unitat = schema.TextLine(title=u"Unitat", description=u"La informació continguda en el camp Unitat, és la corresponent al nom de la unitat a la que pertany, segons consta a gAUSS, la persona que es vol donar d’alta al Cloud Privat UPC. Si la unitat a donar d’alta no és correcte, posi’s en contacte amb l’ATIC al 93 401 62 13.", readonly=True, required=True)
    codiUnitat = schema.TextLine(title=u"Codi Unitat",  description=u"La informació continguda en el camp Codi Unitat, és la corresponent al codi de la unitat a la que pertany, segons consta a gAUSS, la persona que es vol donar d’alta al Cloud Privat UPC. Si la unitat a donar d’alta no és correcte, posi’s en contacte amb l’ATIC al 93 401 62 13.", readonly=True, required=True)    
    email = schema.TextLine(title=u"Correu electrònic institucional",description=u"L’adreça de correu electrònic que s’inclou al formulari és l’adreça institucional que correspon a l’usuari/a. Si l’adreça de correu electrònic no és correcte, posi’s en contacte amb l’ATIC al 93 401 62 13.", readonly=True, required=True)   
    password = schema.Password(title=u"Introdueix la contrasenya", description=u"La contrasenya ha de tenir com a mínim 8 caràcters i ha de contenir dígits (0-9), minúscules (a-z) i majúscules (A-Z).", required=True, min_length=8)
    confirmation = schema.Password(title=u"Repeteix la contrasenya", description=u"Torna a introduir la contrasenya per confirma-la", required=True, min_length=8)

   
    #Valida si la contrasenya conté dígits (0-9), minúscules (a-z) i majúscules (A-Z) i també valida si la contrasenya i la de confirmació son iguals.
    @zope.interface.invariant     
    def check_passwords_match(schema):                            
        """Password and confirmation must match"""  
        #Expressió regular per validar la política de seguretat de la contrasenya 
        tmp = re.compile('^(?=.*\d)(?=.*[a-z])(?=.*([\!\#\$\%\&\+\-\.\?\@\_\€]|[A-Z])).{8,}$').match
        if not tmp(schema.password):            
            raise zope.interface.Invalid("La contrasenya ha de tenir com a mínim 8 caràcters i ha de contenir dígits (0-9), minúscules (a-z) i majúscules (A-Z).")       
        if schema.password != schema.confirmation:                       
            raise zope.interface.Invalid("La seva contrasenya i la de confirmació no coincideixen. Si us plau introduexi-la un altre cop.")
        
    
#Formulari per donar d'alta un usuari al servei Cloud Privat UPC
class AltaCloud(OverridableTemplate, form.Form):   
    index = viewpagetemplatefile.ViewPageTemplateFile('altaCloud.pt')
#    interface.implements(IAltaCloud)
    fields = field.Fields(IAltaCloud)  
    ignoreContext = True # don't use context to get widget data
    label = u"Formulari de registre al servei Cloud Privat UPC"
    
     # Modifico el "common string for use in validation status messages" que utiliza el z3c.form
    formErrorsMessage = _('Hi ha algun error.')   
 
    
    #Pinta automaticament al formulari les dades "nom usuari", "unitat", "codi unitat" i "mail" del ldapUPC 
    def updateWidgets(self):
        super(AltaCloud, self).updateWidgets()         
        portal = getToolByName(self.context,'portal_url').getPortalObject()
        ldapUPC = portal.acl_users.ldapUPC.acl_users
        pm = getToolByName(self.context, 'portal_membership')   
        user_id = pm.getAuthenticatedMember().id           
          
        search_result = [res for res in ldapUPC.searchUsers(cn=user_id,exactMatch=True) if res['cn']==user_id]
        self.widgets['nom_usuari'].value = user_id
        self.widgets['unitat'].value = search_result[0]['unit']
        self.widgets['codiUnitat'].value = search_result[0]['unitCode']        
        if 'mail' in search_result[0]:
            self.widgets['email'].value = search_result[0]['mail']    
        self.widgets.update()
 

    #Guarda automaticament al formulari les dades "nom usuari", "unitat", "codi unitat" i "mail" del ldapUPC 
    def update(self):         
        portal = getToolByName(self.context,'portal_url').getPortalObject()
        ldapUPC = portal.acl_users.ldapUPC.acl_users
        pm = getToolByName(self.context, 'portal_membership')   
        user_id = pm.getAuthenticatedMember().id           
        
        search_result = [res for res in ldapUPC.searchUsers(cn=user_id,exactMatch=True) if res['cn']==user_id]
        self.request.set('nom_usuari', user_id)      
        self.request.set('unitat', search_result[0]['unit'])      
        self.request.set('codiUnitat', search_result[0]['unitCode'])    
        if 'mail' in search_result[0]:
            self.request.set('email', search_result[0]['mail'])     
        return super(AltaCloud, self).update() 
  

    #Botó per donar d'alta a l'usuari
    @button.buttonAndHandler(_(u'Registra usuari'),
                         name='Registra usuari')    
    def handle_proceed(self, action):
        fields = field.Fields(IAltaCloud)    
        schema = IAltaCloud
        
        data, errors = self.extractData()     
      
        #Per poder traduïr els missatges d'error del zope.schema _bootstrapinterfaces.py
        for error in errors:            
            if error.message == ('Required input is missing.'):
                error.message = (u'Camp requerit')  
            elif error.message == ('Value is too short'):
                error.message = (u'El valor és massa curt') 
                
        #Expressió regular per validar la política de seguretat de la contrasenya    
        tmp = re.compile('^(?=.*\d)(?=.*[a-z])(?=.*([\!\#\$\%\&\+\-\.\?\@\_\€]|[A-Z])).{8,}$').match
        #Si hi han errors mostra el missatge d'error 
        #sino envia petició al servei cloud amb les dades necessaries 
        #i redirecciona la resposta al viewlet respostaAltaCloud     
        if errors:  
            if data == {}:
                self.status = self.formErrorsMessage
            elif 'password' not in data:
                self.status = self.formErrorsMessage
            elif 'confirmation' not in data:
                self.status = self.formErrorsMessage
            elif data['password'] != data['confirmation']:             
                formErrorsMessage = _(u"La seva contrasenya i la de confirmació no coincideixen. Si us plau introduexi-la un altre cop.")  
                self.status = formErrorsMessage 
            elif not tmp(data['password']):            
                formErrorsMessage =_(u"La contrasenya ha de tenir com a mínim 8 caràcters i ha de contenir dígits (0-9), minúscules (a-z) i majúscules (A-Z).")
                self.status = formErrorsMessage           
            else:
                self.status = self.formErrorsMessage
        else:   
            nom_usuari = self.request.get('nom_usuari')
            unitat = self.request.get('unitat')
            codiUnitat = self.request.get('codiUnitat')
            email = self.request.get('email')
            password = data['password']            
            url_envio_peticion = 'https://cloud.upc.edu/gestio/plugins/ws/create_user.php'
            valores = '?nom_usuari=%s,unitat=%s,codi_unitat=%s,email=%s,contrasenya=%s' % (nom_usuari,unitat,codiUnitat,email,password)        
            url = url_envio_peticion+valores              
            result_peticion = self.connect_to_server(url) 
            #El primer valor del missatge de resposta "result_peticion" és 1 si l'usuari s'ha creat amb èxit
            #i 0 en qualsevol altre cas
            respuesta_creacion = result_peticion[0]
            mensaje_devuelto = result_peticion[1:]   
            #Si l'usuari s'ha creat amb èxit, guardo les dades de registre en una annotation  
            if respuesta_creacion == '1':
                annotations = IAnnotations(self.context)
#            pruebas pilar
#            registres = annotations.setdefault('upc.cloudPrivat-registres', [])
#            dades_registre = dict(nom_usuari=self.request.get('nom_usuari'),
#                                  unitat=self.request.get('unitat'),
#                                  data=datetime.datetime.now(), 
#                                  resutat=result_peticion,                                 
#                                  )
#            registres.append(dades_registre)               
                    
            #funciona            
                registres = annotations.setdefault('upc.cloudPrivat-registres', {})
                dades_registre = dict(nom_usuari=self.request.get('nom_usuari'),
                                      unitat=self.request.get('unitat'),
                                      codiUnitat = self.request.get('codiUnitat'),
                                      email = self.request.get('email'),
                                      data=datetime.datetime.now(),                                  
                                      )
                registres[self.request.get('nom_usuari')]=dades_registre
                annotations['upc.cloudPrivat-registres']=registres
            #redirecciona la resposta al viewlet respostaAltaCloud            
            return self.request.response.redirect(self.context.portal_url()+'/serveis/servidors-i-xarxes/servidors/cloud-privat-upc/respostaAltaCloud?valor=%s' % mensaje_devuelto)


    
    @button.buttonAndHandler(_(u'Cancel'),
                         name='Cancel')
    def handle_proceed_cancel(self, action):
     self.request.response.redirect(self.context.portal_url()+'/serveis/servidors-i-xarxes/servidors/cloud-privat-upc/')    
       
    def connect_to_server(self, url):
        """Fa una petició via hhtps al servei cloud i retorna el valor retornat pel servei
           Devuelve un stream que es necesario cerrarlo después de usarlo
        """

        data_stream = None
        
        try:
            data_stream = urllib2.urlopen(url, timeout=20)
            xml = data_stream.read()
            data_stream.close()           
        except urllib2.URLError, e:
            raise IOError, e
        except Exception:
            error_message = "Failed contacting server."
            raise RuntimeError, error_message      

        return xml
 

class AltaCloudView(layout.FormWrapper):
     form = AltaCloud
#AltaCloudView = wrap_form(AltaCloud)