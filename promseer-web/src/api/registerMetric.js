import request from '@/utils/request'


export function getRegisterMetric(params) {
  return request({
    url: '/v1/registerMetric',
    method: 'get',
    params
  })
}

export function patchRegisterMetric(id, params) {
  return request({
    url: '/v1/registerMetric/' + id + '/',
    method: 'patch',
    data: params,
    transformRequest: [function (data) {
        let ret = ''
        for (let it in data) {
            ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
        }
        return ret
    }],
  })
}

export function getBackgroundTask(params) {
  return request({
    url: '/background',
    method: 'get',
    params
  })
}

export function rmAction(id, handle, params) {
  return request({
    url:  '/v1/registerMetric/'+id+'/'+handle,
    method: 'get',
    params
  })
}
