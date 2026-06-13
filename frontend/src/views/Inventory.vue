<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>库存管理</span>
          <div style="display:flex;gap:8px">
            <el-upload :show-file-list="false" :before-upload="importInventory" accept=".xlsx">
              <el-button type="success" icon="Upload">Excel导入</el-button>
            </el-upload>
            <el-button type="primary" icon="Plus" @click="openDialog()">录入库存</el-button>
          </div>
        </div>
      </template>
      <el-table :data="inventory" stripe v-loading="loading">
        <el-table-column prop="product_code" label="产品编码" width="120" />
        <el-table-column prop="product_name" label="产品名称" />
        <el-table-column prop="actual_stock" label="实际库存" width="100" align="right" />
        <el-table-column prop="safety_stock" label="安全库存" width="100" align="right" />
        <el-table-column prop="in_transit" label="在途数量" width="100" align="right" />
        <el-table-column prop="wip" label="在制数量" width="100" align="right" />
        <el-table-column label="库存状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.actual_stock >= row.safety_stock ? 'success' : row.actual_stock > 0 ? 'warning' : 'danger'" size="small">
              {{ row.actual_stock >= row.safety_stock ? '充足' : row.actual_stock > 0 ? '偏低' : '缺货' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_updated" label="更新日期" width="110" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑库存' : '录入库存'" width="460px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="产品">
          <el-select v-model="form.product_id" filterable style="width:100%" :disabled="!!form.id">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="实际库存"><el-input-number v-model="form.actual_stock" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="在途数量"><el-input-number v-model="form.in_transit" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="在制数量"><el-input-number v-model="form.wip" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="更新日期"><el-date-picker v-model="form.last_updated" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" /></el-form-item>
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
import { ElMessage } from 'element-plus'
import { inventoryApi, productsApi } from '../api'

const inventory = ref([])
const products = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = ref({})

async function load() {
  loading.value = true
  try {
    const res = await inventoryApi.list()
    inventory.value = res.data
  } finally { loading.value = false }
}

function openDialog(row = null) {
  form.value = row ? { ...row } : { product_id: null, actual_stock: 0, in_transit: 0, wip: 0, last_updated: null, notes: '' }
  dialogVisible.value = true
}

async function save() {
  try {
    if (form.value.id) {
      await inventoryApi.update(form.value.id, form.value)
    } else {
      await inventoryApi.upsert(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } catch (e) { ElMessage.error('保存失败') }
}

async function importInventory(file) {
  try {
    const res = await inventoryApi.import(file)
    ElMessage.success(`导入: 更新${res.data.updated}条`)
    load()
  } catch { ElMessage.error('导入失败') }
  return false
}

onMounted(async () => {
  load()
  const res = await productsApi.list()
  products.value = res.data
})
</script>
