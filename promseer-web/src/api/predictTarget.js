import request from '@/utils/request'

export function getPredictTarget(params) {
  return request({
    url: '/v1/predictTarget',
    method: 'get',
    params
  })
}

export function getImgPredictTarget(id) {
    let url = '/v1/predictTarget/'+id+'/get_pic'
    window.open(url, '_blank','width=800,height=430,menubar=no,toolbar=no')
}

export function deletePredictTarget(id) {
  return request({
    url: '/v1/predictTarget/'+id+'/',
    method: 'delete',
    params: {}
  })
}
