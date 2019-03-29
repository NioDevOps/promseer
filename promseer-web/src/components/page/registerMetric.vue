<template>
  <div>
  <Table
    :columns="columns1"
    :data="data1">
    <template slot-scope="{ row, index }" slot="action">
      <Button
        type="primary"
        size="small"
        style="margin-bottom: 5px"
        :loading="row.train_status == 1"
        @click="()=>{openDlg(row)}">Edit
      </Button>
      <Button
        type="primary"
        size="small"
        style="margin-bottom: 5px"
        :loading="row.train_status == 1"
        @click="predict(row)">Predict
      </Button>
      <Button
        type="primary"
        size="small"
        :loading="row.train_status == 1"
        style="margin-bottom: 5px"
        @click="train_and_predict(row)">Train&Predict
      </Button>
    </template>
  </Table>
  <registerMetricDlg
    ref="registerMetricDlg"
    :form="dlgForm"
    :editModal="dlgEditModal"
    @callback="reload_table">
  </registerMetricDlg>
  </div>
</template>
<script>
  import {getRegisterMetric, getBackgroundTask, rmAction} from '@/api/registerMetric'
  import registerMetricDlg from './registerMetricDlg'
  export default {
    components: { registerMetricDlg },
    data(){
      return {
        dlgEditModal: false,
        dlgForm: {},
        columns1: [
          {
            title: "Name",
            key: "name",
          },
          {
            title: "状态",
            width: 150,
            reload: 0,
            key: "train_status",
            render: (h, params) => {
              let tid = params.row.task_id;
              let status = params.row.train_status;
              if(status != 1){
                params.row.loading = false;
                return h('Icon',
                  {
                    props:{
                      type:"ios-flash-outline",
                      color: status==2 ? "green":"red",
                      size: 24
                    }
                  }
                )
              }
              return h('div',
                [
                  h('Progress',
                    {
                      props:{
                        percent: this.getPercent(tid),
                        status: 'active'
                      }
                    },
                    (this.task_map[tid] != undefined ? this.task_map[tid].ready+" / "+this.task_map[tid].total: "unknow")
                  )
                ]
              )
            }
          },
          {
            title: "训练周期(h)",
            key: "train_period",
          },
          {
            title: "预测周期(h)",
            key: "predict_period",
          },
          {
            title: "最大值",
            key: "max_v",
          },
          {
            title: "最小值",
            key: "min_v",
          },
          {
            title: "weekly预测",
            key: "weekly_seasonality",
          },
          {
            title: "daily预测",
            key: "daily_seasonality",
          },
          {
            title: "创建时间",
            key: "created_t",
          },
          {
            title: "最后变更时间",
            key: "last_modified_t",
          },
          {
              title: 'Action',
              // key: 'action',
              slot: 'action',
              fixed: 'right',
              width: 120,
              // render: (h, params) => {
              //     return h('div', [
              //         h('Button', {
              //             props: {
              //                 type: 'primary',
              //                 size: 'small',
              //                 on:{
              //                   click:()=>{
              //                     console.log(1)
              //                     this.predict(params.row.url)
              //                   }
              //                 },
              //             },
              //             style: {
              //               marginBottom: '5px',
              //             },
              //         }, 'Predict'),
              //         h('Button', {
              //             props: {
              //                 type: 'primary',
              //                 size: 'small',
              //                 on:{
              //                   click:()=>{
              //                     this.train_and_predict(params.row.url)
              //                   }
              //                 },
              //             },
              //             style: {
              //               marginBottom: '5px',
              //             },
              //         }, 'Train&Predict')
              //     ]);
              // }
          }
        ],
        data1: [],
        count: 0,
        task_map:{},
        intervalId: null,
      }
    },
    created(){
      getBackgroundTask()
        .then(
          (response)=>{
            response.results.forEach(
              (v,k)=>{
                this.task_map[v.task_id] = v;
              }
            );
            this.reload_table()
            this.intervalId =setInterval(this.fetchBackGroundTask,10000)
          }
        )
        .catch();
    },
    beforeDestroy () {
        if(this.intervalId!=null){
            clearInterval(this.intervalId)
        }
    },
    methods:{
      reload_table(){
        getRegisterMetric()
            .then(
              (response)=>{
                this.data1 = response.results;
              }
            ).catch();
      },
      fetchBackGroundTask(){
        getBackgroundTask()
        .then(
          (response)=> {
            response.results.forEach(
              (v, k) => {
                this.$set(this.task_map,v.task_id,v);
                console.log(v.task_id,v);
                this.columns1[1].reload += 1
              }
            );
            this.reload_table()
          }
        ).catch(
          (e)=>{
            console.log(e)
          }
        )
      },
       getPercent(tid){
        if(this.task_map[tid] == undefined){
          return 0
        }
        return this.task_map[tid].ready * 100 / this.task_map[tid].total
      },
      train_and_predict(row){
        row.train_status = 1
        rmAction(row.id,'train_background')
          .then(
            ()=>{
              getRegisterMetric()
              .then(
                (response)=>{
                  this.data1 = response.results;
                  this.intervalId =setInterval(this.fetchBackGroundTask,10000)
                }
              ).catch();
            }
          )
          .catch()
      },
      predict(row){
        row.train_status = 1
        rmAction(row.id,'predict_background')
          .then(
            ()=>{
              getRegisterMetric()
                .then(
                  (response)=>{
                    this.data1 = response.results;
                    this.intervalId =setInterval(this.fetchBackGroundTask,10000)
                  }
                ).catch();
            }
          )
          .catch()
      },
      openDlg: function(d) {
        console.log('open dlg')
        this.dlgForm = {}
        this.dlgEditModal = false
        if (d != null) {
          this.dlgForm = d
          this.dlgEditModal = true
        }
        this.$refs.registerMetricDlg.openDlg()
      }
    }
  }
</script>
