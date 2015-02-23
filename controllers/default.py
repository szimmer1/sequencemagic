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
   """Allows a user to view all sequences upon login"""
   seqList = db(db.descriptor_to_user.user_id == auth.user).select(orderby=db.descriptor_table.seq_ID)
   if seqList is None:
      session.flash = T("You have no sequences!")
   return dict(seqList = seqList, user = auth.user)

def view():
   """
   Allows a user to visualize a particular sequence with it's annotations,
   if any are present. Requires seq they want to see to be passed via URL,
   as in sequencemagic/view/seqID
   """
   s = request.args(0) or 'None'
   annotationList = seq = ''
   seqID = db(db.descriptor_table.seqID == s).select().first()
   if seqID is 'None':
      # sequence does not exist
      return dict(seq = seq, annotationList = annotationList)
   seq = db(db.sequences.descriptor_id == seqID).select().seq
   annotationList = db(db.annotations.descriptor_id == seqID).select().annotation_name
   return dict(seq = seq, annotationList = annotationList)

@auth.requires_login()
def upload():
    form = SQLFORM.factory(
        Field('name', label='Sequence name', required=True),
        Field('sequence', 'text', requires=IS_NOT_EMPTY()),
        Field('sequence_file', 'upload'),
        Field('description', 'text')
    )
    new_id = None
    row = None
    if form.process().accepted:
        session.flash = T("Your form was accepted")
        # insert_sequence(form) <-- defined in the
        row = db.sequences.insert(
                            seq=form.vars.sequence
                            )
        new_id = row.id
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
