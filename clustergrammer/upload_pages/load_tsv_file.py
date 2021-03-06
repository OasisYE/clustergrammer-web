def main( buff, inst_filename, mongo_address, viz_id, req_sim_mat=False,
          distance_type='cosine', linkage_type='average'):

  import numpy as np
  import flask
  from bson.objectid import ObjectId
  from pymongo import MongoClient
  from flask import request
  import gridfs
  import json

  # Clustergrammer-PY 5-30-2017 1.13.4 release
  from clustergrammer_py_v1_13_4 import Network

  import StringIO

  client = MongoClient(mongo_address)
  db = client.clustergrammer
  fs = gridfs.GridFS(db)

  viz_id = ObjectId(viz_id)
  found_viz = db.networks.find_one({'_id':viz_id})

  print('in load_tsv_file ' + inst_filename)

  # try:
  print('trying to cluster tsv')

  net = Network()
  net.load_tsv_to_net(buff)

  net.swap_nan_for_zero()

  views = ['N_row_sum', 'N_row_var']

  print('distance type: ' + str(distance_type))
  print('linkage type: ' + str(linkage_type))

  net.cluster(dist_type=distance_type, dendro=True, views=views, \
                 linkage_type=linkage_type, sim_mat=req_sim_mat)

  export_dat = {}
  export_dat['name'] = inst_filename
  export_dat['dat'] = net.export_net_json('dat')
  export_dat['source'] = 'user_upload'

  dat_id = db.network_data.insert(export_dat, check_keys=False)

  update_viz = net.viz
  update_dat = dat_id

  if req_sim_mat:
    update_sim_row = net.sim['row']
    update_sim_col = net.sim['col']

  # except:
  #   print('\nerror in clustering tsv file\n-------------------------\n')
  #   update_viz = 'error'
  #   update_dat = 'error'
  #   if req_sim_mat:
  #     update_sim_row = 'error'
  #     update_sim_col = 'error'

  found_viz['viz'] = update_viz
  found_viz['dat'] = update_dat

  if req_sim_mat:

    sim_row_id = db.networks.insert(update_sim_row, check_keys=False)
    found_viz['sim_row'] = sim_row_id

    sim_col_id = db.networks.insert(update_sim_col, check_keys=False)
    found_viz['sim_col'] = sim_col_id

    # do not directly save sim_row and sim_col to net, save them separately
    # and keep the id with links in net only
    # found_viz['sim_row'] = update_sim_row
    # found_viz['sim_col'] = update_sim_col

  try:
    print('updating document ' + inst_filename)
    db.networks.update_one( {'_id':viz_id}, {'$set': found_viz} )

  except:

    # save viz structure using gridfs
    viz_json_string = json.dumps(found_viz['viz'])
    grid_id = fs.put(viz_json_string)
    found_viz['viz'] = 'saved_to_grid_fs'

    found_viz['grid_id'] = grid_id

    db.networks.update_one( {'_id':viz_id}, {'$set': found_viz} )

  client.close()


