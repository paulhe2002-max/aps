<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>客户订单管理</span>
          <div style="display:flex;gap:8px">
            <el-upload :show-file-list="false" :before-upload="importOrders" accept=".xlsx">
              <el-button type="success" icon="Upload">Excel导入</el-button>
            </el-upload>
            <el-button type="primary" icon="Plus" @click="openDialog()">新建订单</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="12" style="margin-bottom:16px">
        <el-col :span="6">
          <el-select v-model="filterStatus" placeholder="订单状态" clearable @change="load">
            <el-option label="待处理" value="open" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-col>
      </el-row>

      <el-table :data="orders" stripe v-loading="loading">
        <el-table-column prop="order_no" label="订单号" width="140" />
        <el-table-column prop="product_code" label="产品编码" width="120" />
        <el-table-column prop="product_name" label="产品名称" />
        <el-table-column prop="quantity" label="数量" width="90" align="right" />
        <el-table-column prop="due_date" label="交期" width="110" />
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.priority <= 3 ? 'danger' : row.priority <= 6 ? 'warning' : 'info'" size="small">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button text type="danger" @click="deleteOrder(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑订单' : '新建订单'" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="订单号"><el-input v-model="form.order_no" :disabled="!!form.id" /></el-form-item>
        <el-form-item label="产品">
          <el-select v-model="form.product_id" filterable style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.quantity" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="交期"><el-date-picker v-model="form.due_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="form.priority" :min="1" :max="10" style="width:100%" /></el-form-item>
        <el-form-item label="客户"><el-input v-model="form.customer_name" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ordersApi, productsApi } from '../api'

const orders = ref([])
const products = ref([])
const loading = ref(false)
const filterStatus = ref('')
const dialogVisible = ref(false)
const form = ref({})

const statusType = (s) => ({ open: 'primary', in_progress: 'warning', completed: 'success', cancelled: 'danger' }[s] || '')
const statusLabel = (s) => ({ open: '待处理', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }[s] || s)

async function load() {
  loading.value = true
  try {
    const res = await ordersApi.list({ status: filterStatus.value || undefined })
    orders.value = res.data
  } finally { loading.value = false }
}

async function loadProducts() {
  const res = await productsApi.list()
  products.value = res.data
}

function openDialog(row = null) {
  form.value = row ? { ...row } : { order_no: '', product_id: null, quantity: 1, due_date: '', priority: 5, customer_name: '', notes: '' }
  dialogVisible.value = true
}

async function save() {
  try {
    if (form.value.id) {
      await ordersApi.update(form.value.id, form.value)
    } else {
      await ordersApi.create(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function deleteOrder(id) {
  await ElMessageBox.confirm('确认删除?', '警告', { type: 'warning' })
  await ordersApi.delete(id)
  ElMessage.success('已删除')
  load()
}

async function importOrders(file) {
  try {
    const res = await ordersApi.import(file)
    ElMessage.success(`导入成功: ${res.data.created}条, 跳过: ${res.data.skipped}条`)
    load()
  } catch { ElMessage.error('导入失败') }
  return false
}

onMounted(() => { load(); loadProducts() })
</script>
