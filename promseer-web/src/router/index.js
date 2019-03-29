import Vue from 'vue';
import Router from 'vue-router';

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/',
            component: resolve => require(['../components/common/index.vue'], resolve),
            children: [
                {
                    path: '/registerMetric',
                    component: resolve => require(['../components/page/registerMetric.vue'], resolve)
                },
                {
                    path: '/predictTarget',
                    component: resolve => require(['../components/page/predictTarget.vue'], resolve)
                }
            ]
        }
    ]
})
