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
   user = all_descriptors = None
   header_text = "Latest sequences"
   
   """Set response menu"""
   ctrl = 'index'
   authorized = False
   if request.args(0) is not None:
       ctrl = 'myindex'
       header_text = "My sequences"
       if request.args(0) != 'None':
           p = db(db.descriptor_table.creating_user_id == request.args(0)).select()
           for row in p:
               if row.creating_user_id == auth.user_id:
                   authorized = True  
       else:
           session.flash = T("You need to login!")

   #response.menu = setResponseMenu('index', True)
   response.menu = setResponseMenu(ctrl, authorized)

   # TODO: conditional authorization for viewing "My sequences"

   """If passed arg (user id), shows only user's sequences (requires auth). Else, shows all sequences"""

   # seqList = db(db.descriptor_to_user.user_id == auth.user_id).select(orderby=db.descriptor_table.seq_id)
   user = auth.user
   all_descriptors = db().select(db.descriptor_table.ALL, orderby=~db.descriptor_table.date_created) # For now, return all descriptors in the DB
   query = None
   if authorized: #only showing the sequences you created and that you are subscribed without the edit button
       #all_descriptors = db(db.descriptor_table.creating_user_id == request.args(0)).select(db.descriptor_table.ALL)
       query = db(db.descriptor_to_user.user_id == request.args(0)).select(db.descriptor_to_user.descriptor_id)
       #query is to get all the sequence_id subscribed to the user_id
       
   if all_descriptors is None:
      session.flash = T("You have no sequences!")
   
  
   
   return locals()

@auth.requires_login()
def subscribe():
    checking = db((db.descriptor_to_user.descriptor_id == request.args(0)) & (db.descriptor_to_user.user_id == auth.user_id)).select(db.descriptor_to_user.ALL)
    if not checking:
        update_descriptor_to_user(request.args(0))   
    
    
    redirect(URL('default', 'index'))    

@auth.requires_login()
def edit():
    # authorize the user to edit
    authorized = False
    if request.args(0) is not None:
       header_text = "You're not authorized to edit this sequence"
       p = db(db.descriptor_table.id == request.args(0)).select()
       for row in p:
          if row.creating_user_id == auth.user_id:
              authorized = True
              header_text = row.sequence_name
          else:
              session.flash = T("You need to login!")
    else:
        redirect(URL('default', 'index'))

    sequence_name = "Test sequence"

    return locals()

def view():
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

    categories = ["fasta", "seq"]
    form_text = SQLFORM.factory(
        Field('name', label='Sequence name', required=True),
        Field('seqs', 'text', requires=IS_NOT_EMPTY()),
        Field('description', 'text')
    )
    form_file = SQLFORM.factory(
        Field('name', label='Sequence name', required=True),
        Field('sequence_file', 'upload', required=True),
        Field('description', 'text')
    )

    if form_text.process().accepted:
        session.flash = T("Your form was accepted")
        insert = insert_sequence(form_text)
        descriptor_id = insert['desc_id'] #<-- defined in the models
        redirect(URL('default', 'index'))

    elif form_file.process().accepted:
        session.flash = T("Your form was accepted")
        insert = insert_sequence(form_file)
        descriptor_id = insert['desc_id'] #<-- defined in the models
        redirect(URL('default', 'index'))
        
     #redirect(URL('default', 'view', vars=dict(sequenceid=seq_id))
        
    else:
        pass
    return locals()


"""This is just to test the tables and probably not how we should do this"""
@auth.requires_login()
def upload_annotation():
    """Set response menu"""
    # response.menu = setResponseMenu('multiple', True)

    categories = []
    for seq in db(db.descriptor_table).select(): #run through seq names
        """if auth.user.first_name == seq.creating_user_id: #if they match curr users name append them for later
            categories.append(seq.sequence_name)"""
        categories.append(seq.sequence_name)

    form = SQLFORM.factory(
        Field('seq_name', label=' Select A Sequence to Annotate', requires=IS_IN_SET(categories), required=True), # consists of only users own sequences
        Field('annotation_name', requires=IS_NOT_EMPTY()),
        Field('annotation_position', 'list:integer'),
        Field('description', 'text')
    )

    if form.process().accepted:
        session.flash = T("Your form was accepted")
        descriptor_id = insert_annotation(form) #<-- defined in the models
        redirect(URL('default', 'view', args=[descriptor_id]))
    else:
        pass
    return dict(form=form)

"""Done just needs tweaking based on UI"""
def search():
    search_seq = request.vars.search
    search_pages = []
    search_page_ids = []
    if search_seq is not None:
        all_pages = db().select(db.descriptor_table.ALL, orderby=db.descriptor_table.sequence_name)
        for page in all_pages:
            if (search_seq.lower() in repr(page.sequence_name).lower()):
                search_page_ids.append(page.id)
                search_pages.append(page)
    return dict(search_seq=search_seq, search_pages=search_pages, search_page_ids=search_page_ids)

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
