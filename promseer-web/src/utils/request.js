import axios from 'axios'
import { Message, MessageBox } from 'iview'
axios.defaults.headers.common['Content-Type'] = "application/json"
// 创建axios实例
const service = axios.create({
  baseURL: process.env.BASE_API, // api的base_url
  timeout: 30000      ,            // 请求超时时间
  headers:{'Content-Type':"application/x-www-form-urlencoded"}
})

// request拦截器
// service.interceptors.request.use(config => {
//   if (store.getters.token) {
//     //config.headers['X-Token'] = getToken() // 让每个请求携带自定义token 请根据实际情况自行修改
//
//   }
//   return config
// }, error => {
//   // Do something with request error
//   console.log(error) // for debug
//   Message({
//       message:"连接nobita接口失败",
//       type: 'error',
//       duration: 5 * 1000
//     })
//   Promise.reject(error)
// })

// respone拦截器
service.interceptors.response.use(
  response => {
  /**
  * code为非20000是抛错 可结合自己业务进行修改
  */
    return response.data
  },
  error => {
    console.log(error)// for debug
    if(error.response==undefined){
      Message({
        message:"连接venus后端失败",
        type: 'error',
        duration: 5 * 1000
     })
    }else{
      Message({
        message:error.response.data.message ||"访问后端接口连接失败",
        type: 'error',
        showClose: true,
        duration: 5 * 1000
      })
    }
    return Promise.reject(error)
  }
)

export default service
