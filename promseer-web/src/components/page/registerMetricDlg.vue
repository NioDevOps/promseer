<template>
  <Modal
    title="register metric"
    v-model="visible"
    width="50%"
    @on-ok="submit_edit_form"
    @on-cancel="closeDlg">
    <Form
      ref="form"
      :rules="rules"
      :model="form">
      <FormItem
        prop="name"
        label="name">
        <Input
          v-model="form.name">
        </Input>
      </FormItem>
      <FormItem
        prop="cron"
        label="定时训练">
        <Input
          v-model="form.cron">
        </Input>
      </FormItem>
      <FormItem
        prop="metric"
        label="metric">
        <Input
          v-model="form.metric">
        </Input>
      </FormItem>
      <FormItem
        type="number"
        prop="train_period"
        label="训练周期">
        <Input
          v-model="form.train_period">
        </Input>
      </FormItem>
      <FormItem
        type="number"
        prop="predict_period"
        label="预测周期">
        <Input
          v-model="form.predict_period">
        </Input>
      </FormItem>
    </Form>
  </Modal>
</template>
<script>
  import {patchRegisterMetric} from '@/api/registerMetric'
  export default {
    props: {
      form: {
        default: () => {
          return {}
        }, type: Object
      },
      editModal: { default: false, type: Boolean }
    },
    data() {
      return {
        visible: false,
        title: '',
        rules: {
          name: [{ required: true, message: '请输入', trigger: 'blur' }],
          cron: [{ required: false, message: '请输入', trigger: 'blur' }],
          metric: [{ required: true, message: '请输入', trigger: 'blur' }],
          train_period: [{ required: false, message: '请输入', trigger: 'blur' }],
          predict_period: [{ required: false, message: '请输入', trigger: 'blur' }],
        }
      }
    },
    methods: {
      openDlg() {
        this.visible = true
      },
      closeDlg() {
        this.visible = false
      },
      submit_edit_form() {
        this.$refs['form'].validate((valid) => {
          if (valid) {
            delete this.form.max_v
            delete this.form.min_v
            if (!this.form.cron) {
              this.form.cron = ""
            }
            patchRegisterMetric(this.form.id, this.form)
              .then(() => {
                this.closeDlg()
                this.$Message.info('修改成功')
              })
          } else {
            this.$Message.error('信息必须全部填写')
          }
        })
      }
    }
  }
</script>

