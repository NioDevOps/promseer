<template>
  <div>
    <Input
      placeholder="Search"
      v-model="search"
      @on-change="(e)=>{this.load()}"
      style="width:50% ;margin-bottom: 10px;">
      <Icon
        type="ios-search"
        slot="suffix">
      </Icon>
    </Input>
    <Table
    :columns="columns1"
    :data="data1">
      <template slot-scope="{ row, index }" slot="labels">
        <Tag
          v-for="(v,k) in row.labels"
          :key="k"
        >{{v.k+"="+v.v}}
        </Tag>
      </template>
      <template slot-scope="{ row, index }" slot="action">
        <Button
        type="primary"
        size="small"
        style="margin-bottom: 5px"
        :loading="row.loading == true"
        @click="predict(row.id)">Predict
        </Button>
        <Button
          type="error"
          size="small"
          style="margin-bottom: 5px"
          :loading="row.loading == true"
          @click="pt_delete(row.id)">Delete
        </Button>
      </template>
    </Table>
    <Page
    :total="total"
    :current="current"
    @on-change="load"
    show-total />
  </div>
</template>
<script>
  import {getPredictTarget, getImgPredictTarget, deletePredictTarget} from '@/api/predictTarget'
  export default {
    data(){
      return {
        total: 0,
        search: "",
        current: 1,
        columns1: [
          // {
          //   title: "Labels",
          //   key: "labels",
          //   render: (h, params) => {
          //     let lbs = [];
          //     console.log(params.row.labels)
          //     params.row.labels.forEach(
          //       (v,k)=>{
          //         lbs.push(
          //           h('Tag',
          //             {
          //               props:{
          //                 color: 'default'
          //               }
          //             },
          //             v.k+"="+v.v
          //           )
          //         )
          //       }
          //     );
          //     return h('div',
          //       lbs
          //     );
          //   }
          // },
          {
            title: "Labels",
            key: "labels",
            slot: "labels",
          },
          {
            title: "metric id",
            key: "register_metric",
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
          }
        ],
        data1: [],
        count: 0
      }
    },
    created(){
      this.load()
    },
    methods:{
      load(p){
        let pp = this.current;
        if(p!=undefined){
          pp = p;
        }
        getPredictTarget({page: pp, search: this.search})
        .then(
          (response)=>{
            this.data1 = response.results;
            this.total = response.count;
            this.columns.push();
          }
        )
        .catch()
      },
      predict(id){
        getImgPredictTarget(id)
      },
      pt_delete(id) {
        this.$Modal.confirm({
          title: '确认操作',
          content: '<p>将要删除此条数据，确认删除？</p>',
          onOk: () => {
            deletePredictTarget(id).then(() => {
                this.load()
                this.$Message.info('删除成功')
              }
            )
          },
          onCancel: () => {
            this.$Message.info('取消');
          }
        });
      }
    }
  }
</script>
