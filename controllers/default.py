# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################

import gluon.contrib.simplejson as json
import os

def index():
   user = all_descriptors = None
   header_text = "Latest sequences"
   search = False
   search_seq = ""
   search_pages = []
   
   """Set response menu"""
   ctrl = 'index'
   authorized = False
   empty_query = None
   
   
   if request.vars.search_seq is not None:
       header_text = "Search Results"
       search = True
       search_seq = request.vars.search_seq
       if request.vars.search_pages is not None:
           if len(request.vars.search_pages) > 0:
               all_pages = db().select(db.descriptor_table.ALL, orderby=db.descriptor_table.sequence_name)
               for page in all_pages:
                   if (search_seq.lower() in repr(page.sequence_name).lower()):
                       search_pages.append(page)
               return locals()
       else: # no search results found
           search_pages = None
           return locals()
   if request.args(0) is not None:
       ctrl = 'myindex'
       header_text = "My sequences"
       if request.args(0) != 'None':
           p = db(db.descriptor_to_user.user_id == request.args(0)).select()
           for row in p:

               if row.user_id== auth.user_id:
                   authorized = True 
        
           
           if not authorized: 
               if request.args(0) == str(auth.user_id): #doing this to ensure the user is the one that the url says 
                   authorized = True               #(you can manually change it. this fixes that)
                   empty_query = True
                   

           """if p is None:
               session.flash = T("You need to subscribe")"""

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
def unsubscribe():
	items = db((db.descriptor_table.id==request.args(0))).select()
	for item in items:
		if item.creating_user_id==auth.user_id:
			session.flash = T("You can not unsubscribe from a sequence you created.")
			redirect(URL('default', 'index', vars={'test':'test'}))
	#in tools.py
	delete_subscription(request.args(0))
	redirect(URL('default', 'index', args = [auth.user_id]))

@auth.requires_login()
def edit():
    # authorize the user to edit
    authorized = False
    sequence_name = 'Unknown sequence'
    if request.args(0) is not None:
       header_text = "You're not authorized to edit this sequence"
       p = db(db.descriptor_table.id == request.args(0)).select().first()
       if p.creating_user_id == auth.user_id:
              authorized = True
              header_text = sequence_name = p.sequence_name
       else:
              session.flash = T("You need to login!")
    else:
        redirect(URL('default', 'index'))

    seq_row = file_url = None
    if authorized:
        seq_row = db(db.sequences.id == p.seq_id).select().first()
        if seq_row is not None and seq_row.seq_file_type == 'FASTA':
            file_url = URL('static', 'uploads', args=[seq_row.seq_file_name], scheme=True, host=True)
        else:
            session.flash = T("Couldn't find a sequence for the given descriptor ID")

    return locals()

def view():
   # Helper functions
   def abbreviation(string):
      r = ""
      l = string.split(" ")
      if len(l) < 2:
          return string
      for w in l:
          if not isinstance(w,str):
              continue
          pass
          r += w[0].upper()
      return r

   """Plasmid functions"""
   def labelFreq(length):
       if length < 500:
          return 50
       elif length < 1000:
          return 100
       elif length < 5000:
           return 500
       else:
           return 5000

   def getAvoids(annotation_dict):
       flat_annotation_list = []
       avoids = []
       # flatten annotation_list
       for userid, annotations_list in annotation_dict.iteritems():
           flat_annotation_list.extend(annotations_list)
       # initialize avoids array
       for i in range(len(flat_annotation_list)):
           avoids.append(0)

       # compare annotations
       for index, this_annotation in enumerate(flat_annotation_list):
           compare_annotations = flat_annotation_list[(index+1):]
           for an_annotation in compare_annotations:
              if this_annotation.annotation_location[0] < (an_annotation.annotation_location[0] + an_annotation.annotation_length) \
              or (this_annotation.annotation_location[0] + this_annotation.annotation_length) > an_annotation.annotation_location[0]:
                 if avoids[index] == 0:
                     avoids[index] = 1
                 else:
                     avoids[index] = 0

       return avoids


   """
   Allows a user to visualize a particular sequence with it's annotations,
   if any are present. Requires seq they want to see to be passed via URL,
   as in sequencemagic/view/:descriptor_id
   """
   annotationList = sequence_row = seq = seq_type = desc_name = \
       desc_description = date_created = desc_author = list_of_subscriptors = \
       seq_length = annotation_list = plasmid_name = user_chosen = \
       selected_user_id = annotation_form = is_subscriptor = is_creator = \
       update_sequence_form = avoid = None
   found_sequence = False
   
   desc_id = request.args(0) or None
   if desc_id is None:
       # no descriptor id given
       return locals()

   desc_row = db(db.descriptor_table.id == desc_id).select().first()

   if desc_row is None:
       # descriptor doesn't exist
       seq = 'Sequence not found for given descriptor ID'
       return locals()

   user_row = db(db.auth_user.id == desc_row.creating_user_id).select().first()

   desc_author = user_row.first_name + " " + user_row.last_name
   desc_name = desc_row.sequence_name
   desc_description = desc_row.sequence_description
   date_created = desc_row.date_created
   seq_id = desc_row.seq_id

   sequence_row = db(db.sequences.id == seq_id).select().first()
   if sequence_row.seq is not None:
       found_sequence = True
       seq = sequence_row.seq
       seq_type = 'text'
   elif sequence_row.seq_file_name is not None:
       found_sequence = True
       seq = sequence_row.seq_file_name
       seq_type = sequence_row.seq_file_type

   if seq is None:
       # sequence info is corrupted/missing
       seq = 'Sequence info not found'
       return locals()

   # authorize the user to edit
   authorized = False
   if seq is not None:
      header_text = "You're not authorized to edit this sequence"
      
      pq = db((db.descriptor_to_user.descriptor_id == desc_id)&(db.descriptor_to_user.user_id == db.auth_user.id)&(db.descriptor_to_user.descriptor_id == db.descriptor_table.id)).select(db.descriptor_table.ALL, db.descriptor_to_user.ALL)
      for p in pq:
          if p.descriptor_to_user.user_id == auth.user_id:
                 authorized = True
                 is_subscriptor = True
                 if p.descriptor_table.creating_user_id == auth.user_id:
                     is_creator = True
                 header_text = sequence_name = p.descriptor_table.sequence_name
                 if len(sequence_name.split(" ")) > 1:
                     plasmid_name = abbreviation(sequence_name)
                 else:
                     plasmid_name = sequence_name
          else:
             session.flash = T("You need to login!")
   else:
       return locals()

   sequence_row = file_url = None
   
   
       # get sequence length and annotation data
   seq_length = len(seq.replace(" ", ""))
   if request.vars.user_id is not None:
        selected_user_id = long(request.vars.user_id+"L")
        user_chosen = True
   pass
   
   '''Query for Active Annotations''' #annotation_list used in view
   list_of_subscriptors = db((db.descriptor_to_user.descriptor_id == desc_id) & (db.descriptor_to_user.user_id == db.auth_user.id)).select(db.auth_user.ALL, orderby=db.auth_user.id)
   annotation_list = {} #(dict)
   active_id_list = []  #(list)

   for subscriptor in list_of_subscriptors:
       annotation_list[subscriptor.id] = []
   for active_annotation in db(db.active_annotations.descriptor_id==desc_id).select():
       active_id_list.append(active_annotation.active_id)
   for active_id in active_id_list:
       annotation_row = db(db.annotations.id==active_id).select()
       for annotation in annotation_row:
           #if annotation.creating_user_id in annotation_list:
           if annotation_list.has_key(annotation.creating_user_id):
               annotation_list[annotation.creating_user_id].append(db(db.annotations.id==active_id).select().first())
   pass

   avoid = getAvoids(annotation_list)


   '''Annotation Update History''' #annotation_history list used in view
   annotation_id_list = []
   annotation_history = []
   for annotation in db(db.annotation_to_descriptor.descriptor_id==desc_id).select():
      annotation_id_list.append(annotation.annotation_id)
   annotation_id_list.sort(reverse=True)
   for annot_id in annotation_id_list:
      annotation_history.append(db(db.annotations.id==annot_id).select().first())

   
   """Add annotation form"""
   if authorized and seq is not None:
      annotation_form = SQLFORM.factory(
          Field('seq_name', writable=False, readable=False),
          Field('annotation_name', requires=IS_NOT_EMPTY()),
          Field('annotation_position', 'list:integer'),
          Field('length', 'integer'),
          Field('description', 'text'),
          table_name='annotation_table'
      )
      annotation_form.vars.seq_name = sequence_name

      if annotation_form.process().accepted:
          session.flash = T("Your form was accepted")
          descriptor_id = insert_annotation(annotation_form) #<-- defined in the models
          redirect(URL('default', 'view', args=[descriptor_id]))
      else:
          pass

      """Update Sequence Form"""
      update_sequence_form = SQLFORM.factory(
              Field('name', readable=False),
              Field('seqs', 'text', label='Additional Sequence to Add', requires=IS_NOT_EMPTY()),
              Field('position', label='Position(s) to Insert Sequence'),
              Field('form_action', readable=False)
          )
      update_sequence_form.vars.form_action = 'add'
      update_sequence_form.vars.name = sequence_name

      if update_sequence_form.process().accepted:
          session.flash = T("Your form was accepted")
          if update_sequence_form.vars.form_action == 'add':
              update_existing_sequence(update_sequence_form,'add')
              redirect(URL('default', 'view',
                           args=db(db.descriptor_table.sequence_name==update_sequence_form.vars.name).select().first().id))
          elif update_sequence_form.vars.form_action == 'replace':
              update_existing_sequence(update_sequence_form,'replace')
              redirect(URL('default', 'view',
                           args=db(db.descriptor_table.sequence_name==update_sequence_form.vars.name).select().first().id))
          else:
              length = update_existing_sequence(update_sequence_form,'del')
              redirect(URL('default', 'view',
                           args=db(db.descriptor_table.sequence_name==update_sequence_form.vars.name).select().first().id))

   """Last updated queries"""
   query_last_annotator = db((db.descriptor_table.id == desc_id) & (db.descriptor_table.id == db.annotation_to_descriptor.descriptor_id) & (db.annotation_to_descriptor.annotation_id == db.annotations.id) & (db.annotations.creating_user_id == db.auth_user.id)).select(db.annotations.creating_user_id, db.annotations.date_created, db.auth_user.first_name, db.auth_user.last_name, orderby=~db.annotations.date_created)
   last_annotator = None
   for row in query_last_annotator:
       last_annotator = row
       break
   
   return locals()


@auth.requires_login()
def upload():
    """Set response menu"""
    response.menu = setResponseMenu('upload', True)

    categories = ["FASTA", "Plain Sequence"]
    file_active = True;
    form = SQLFORM.factory(
        Field('name', label='Sequence name', required=True),
        Field('file_type', label = "File Type", requires=IS_IN_SET(categories)),
        Field('sequence_file', 'upload', uploadfolder=request.folder+'/static/uploads'),
        Field('description', 'text'),
		csv = False
    )
    #form.add_button('Enter Sequence Manually', URL('upload', args=['man']))
    
	#Manual Sequence Entry form
    if request.args(0)=='man':
        file_active = False;
        form = SQLFORM.factory(
            Field('name', label = 'Sequence name', required = True),
            Field('seqs', 'text', requires=IS_NOT_EMPTY()),
            Field('description', 'text'),
			csv = False
        )
        #form.add_button('Enter Sequence File', URL('upload', args=[]))

    if form.process().accepted:
        session.flash = T("Your form was accepted")
        if request.args(0)=='man':
            insert = insert_man_sequence(form)
            descriptor_id = insert['desc_id'] #<-- defined in the models
            redirect(URL('default', 'index'))
     	else: 
            insert = insert_file_sequence(form)
            descriptor_id = insert['desc_id'] #<-- defined in the models
            redirect(URL('default', 'index'))
     
	 #redirect(URL('default', 'view', vars=dict(sequenceid=seq_id))
    return locals()


"""This is just to test the tables and probably not how we should do this"""
@auth.requires_login()
def upload_annotation():
    """Set response menu"""
    # response.menu = setResponseMenu('multiple', True)

    categories = []
    subscribed_descriptors = db(db.descriptor_to_user.user_id == auth.user_id).select(db.descriptor_to_user.descriptor_id)
    for descriptor in subscribed_descriptors: #run through seq names
        seq = db(db.descriptor_table.id == descriptor.descriptor_id).select(db.descriptor_table.sequence_name).first()
        categories.append(seq.sequence_name)

    form = SQLFORM.factory(
        Field('seq_name', label=' Select A Sequence to Annotate', requires=IS_IN_SET(categories), required=True), # consists of only users own sequences
        Field('annotation_name', requires=IS_NOT_EMPTY()),
        Field('annotation_position', 'list:integer'),
        Field('length', 'integer'),
        Field('description', 'text'),
		csv = False
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
    redirect(URL('default', 'index', vars=dict(search_seq=search_seq,
                                               search_pages=search_pages)))


'''only sequence uploader may delete sequence'''
@auth.requires_login()
def delete():
    desc_id = request.vars.desc_id
    annotation_id = request.vars.annotation_id
    annotations = None
    # check user permissions
    if desc_id:
        if auth.user.id <> db(db.descriptor_table.id==desc_id).select().first().creating_user_id:
			session.flash=T('Invalid Privileges')
			redirect(URL('default', 'index'))
    elif annotation_id:
        if auth.user.id <> db(db.annotations.id==annotation_id).select().first().creating_user_id:
			test = db(db.annotations.id==annotation_id).select().first().creating_user_id
			session.flash=T('Invalid Privileges')
			redirect(URL('default', 'index'))
	
	'''deleting sequence+associated annotations'''		
    if desc_id:
		#in tools.py
		delete_sequence(desc_id)
	
    '''deleting single annotation with given annotation id'''
    if annotation_id:
		#in tools.py
		delete_annotation(annotation_id)
    

    return

'''Anyone subscribed to sequence may edit annotations
def delete_annotation(annotation_id):
		#delete annotations tuple
		#delete annotation_to_descriptors
	return
'''

def update_sequence():
    """Set response menu"""
    # response.menu = setResponseMenu('upload', True)

    categories = []
    del_active = True
    add_active = False

    for seq in db(db.descriptor_table).select(): #run through seq names
        if (seq.creating_user_id == auth.user_id):
            categories.append(seq.sequence_name)

    form = SQLFORM.factory(
        Field('name', label='Select a Sequence', requires=IS_IN_SET(categories), required=True),
        Field('position', label='Location to Delete')
    )

    if request.args(0)=='add':
        del_active = False
        add_active = True
        form = SQLFORM.factory(
            Field('name', label='Select a Sequence to Add to', requires=IS_IN_SET(categories), required=True),
            Field('seqs', 'text', label='Additional Sequence to Add', requires=IS_NOT_EMPTY()),
            Field('position', label='Position(s) to Insert Sequence')
        )
    if request.args(0)=='replace':
        del_active = False
        add_active = False
        form = SQLFORM.factory(
            Field('name', label='Select a Sequence', requires=IS_IN_SET(categories), required=True),
            Field('seqs', 'text', label='Replacement Sequence', requires=IS_NOT_EMPTY()),
            Field('position', label='Position(s) to replace with above Sequence')
        )

    if form.process().accepted:
        session.flash = T("Your form was accepted")
        if request.args(0)=='add':
            update_existing_sequence(form,'add')
            redirect(URL('default', 'view',
                         args=db(db.descriptor_table.sequence_name==form.vars.name).select().first().id))
        elif request.args(0)=='replace':
            update_existing_sequence(form,'replace')
            redirect(URL('default', 'view',
                         args=db(db.descriptor_table.sequence_name==form.vars.name).select().first().id))
     	else:
            length = update_existing_sequence(form,'del')
            redirect(URL('default', 'view',
                         args=db(db.descriptor_table.sequence_name==form.vars.name).select().first().id))
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
