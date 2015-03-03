# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################

def index():
   """Set response menu"""
   ctrl = 'index'
   authorized = False
   if request.args(0) is not None:
       ctrl = 'myindex'
       # determine in authorized is true or false
   response.menu = setResponseMenu(ctrl, authorized)

   # TODO: conditional authorization for viewing "My sequences"

   user = all_descriptors = None

   """If passed arg (user id), shows only user's sequences (requires auth). Else, shows all sequences"""

   # seqList = db(db.descriptor_to_user.user_id == auth.user_id).select(orderby=db.descriptor_table.seq_id)
   user = auth.user
   all_descriptors = db().select(db.descriptor_table.ALL) # For now, return all descriptors in the DB
   if all_descriptors is None:
      session.flash = T("You have no sequences!")
   return locals()

def view():
   """Set response menu"""
   response.menu = setResponseMenu('view', False)

   """
   Allows a user to visualize a particular sequence with it's annotations,
   if any are present. Requires seq they want to see to be passed via URL,
   as in sequencemagic/view/:descriptor_id
   """
   annotationList = seq = desc_name = desc_description = date_created = desc_author = None

   desc_id = request.args(0) or None
   if desc_id is None:
       # no descriptor id given
       return locals()

   desc_row = db(db.descriptor_table.id == desc_id).select().first()
   user_row = db(db.auth_user.id == desc_row.creating_user_id).select().first()

   desc_author = user_row.first_name + " " + user_row.last_name
   desc_name = desc_row.sequence_name
   desc_description = desc_row.sequence_description
   date_created = desc_row.date_created
   seq_id = desc_row.seq_id

   seq = db(db.sequences.id == seq_id).select().first().seq
   if seq_id is None or seq is None:
       # sequence doesn't exist
       return locals()

   # annotationList = db(db.annotations.descriptor_id == seqID).select().annotation_name
   return locals()

@auth.requires_login()
def upload():
    """Set response menu"""
    response.menu = setResponseMenu('upload', True)

    form = SQLFORM.factory(
        Field('name', label='Sequence name', required=True),
        Field('seqs', 'text', requires=IS_NOT_EMPTY()),
        #Field('sequence_file', 'upload'),
        Field('description', 'text')
    )

    if form.process().accepted:
        session.flash = T("Your form was accepted")
        descriptor_id = insert_sequence(form) #<-- defined in the models
        redirect(URL('default', 'view', args=[descriptor_id]))
    else:
        pass
    return locals()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
