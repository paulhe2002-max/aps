<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="产线管理" name="lines">
        <el-row :gutter="16">
          <el-col :span="10">
            <el-card>
              <template #header>
                <div style="display:flex;justify-content:space-between">
                  <span>产线列表</span>
                  <el-button type="primary" size="small" @click="openLineDialog()">新建产线</el-button>
                </div>
              </template>
              <el-table :data="lines" @row-click="selectLine" highlight-current-row size="small">
                <el-table-column prop="code" label="编码" width="80" />
                <el-table-column prop="name" label="名称" />
                <el-table-column prop="shifts_per_day" label="班次" width="60" align="center" />
                <el-table-column prop="capacity_per_shift" label="产能/班" width="80" align="right" />
                <el-table-column label="操作" width="70">
                  <template #default="{ row }">
                    <el-button text size="small" type="primary" @click.stop="openLineDialog(row)">编辑</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :span="14" v-if="selectedLine">
            <el-card>
              <template #header>
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <span>{{ selectedLine.name }} - 产品工艺</span>
                  <el-button type="primary" size="small" @click="openLpDialog()">绑定产品</el-button>
                </div>
              </template>
              <el-table :data="lineProducts" size="small">
                <el-table-column prop="product_code" label="产品编码" width="100" />
                <el-table-column prop="product_name" label="产品名称" />
                <el-table-column prop="cycle_time_minutes" label="节拍(分钟)" width="100" align="right" />
                <el-table-column prop="setup_time_minutes" label="换型(分钟)" width="100" align="right" />
                <el-table-column prop="cost_per_unit" label="单位成本" width="90" align="right" />
                <el-table-column label="操作" width="70">
                  <template #default="{ row }">
                    <el-button text type="danger" size="small" @click="deleteLp(row.id)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="工作日历" name="calendar">
        <el-card v-if="selectedLine">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ selectedLine?.name }} - 工作日历</span>
              <div style="display:flex;gap:8px">
                <el-date-picker v-model="calRange" type="daterange" value-format="YYYY-MM-DD"
                  start-placeholder="开始" end-placeholder="结束" style="width:260px" />
                <el-input-number v-model="genShifts" :min="0" :max="3" placeholder="班次" style="width:80px" />
                <el-button type="success" @click="generateCal">生成日历</el-button>
              </div>
            </div>
          </template>
          <el-table :data="calendar" size="small" max-height="400">
            <el-table-column prop="work_date" label="日期" width="110" />
            <el-table-column prop="shift_count" label="班次" width="60" align="center" />
            <el-table-column prop="available_hours" label="可用工时" width="90" align="right" />
            <el-table-column label="是否休息" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_holiday ? 'danger' : 'success'" size="small">
                  {{ row.is_holiday ? '休息' : '工作' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-empty v-else description="请在产线管理中选择产线" />
      </el-tab-pane>

      <el-tab-pane label="换型时间" name="changeover">
        <el-card v-if="selectedLine">
          <template #header>
            <div style="display:flex;justify-content:space-between">
              <span>{{ selectedLine?.name }} - 换型时间矩阵</span>
              <el-button type="primary" size="small" @click="openCoDialog()">添加换型</el-button>
            </div>
          </template>
          <el-table :data="changeovers" size="small">
            <el-table-column prop="from_product_name" label="从产品" />
            <el-table-column prop="to_product_name" label="至产品" />
            <el-table-column prop="changeover_minutes" label="换型时间(分钟)" align="right" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button text type="danger" size="small" @click="deleteCo(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        <el-empty v-else description="请在产线管理中选择产线" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="lineDialog" :title="lineForm.id ? '编辑产线' : '新建产线'" width="440px">
      <el-form :model="lineForm" label-width="100px">
        <el-form-item label="编码"><el-input v-model="lineForm.code" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="lineForm.name" /></el-form-item>
        <el-form-item label="班次数"><el-input-number v-model="lineForm.shifts_per_day" :min="1" :max="3" style="width:100%" /></el-form-item>
        <el-form-item label="产能/班(小时)"><el-input-number v-model="lineForm.capacity_per_shift" :min="1" :max="24" style="width:100%" /></el-form-item>
        <el-form-item label="工人/班"><el-input-number v-model="lineForm.workers_per_shift" :min="1" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="lineDialog=false">取消</el-button>
        <el-button type="primary" @click="saveLine">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="lpDialog" title="绑定产品工艺" width="400px">
      <el-form :model="lpForm" label-width="100px">
        <el-form-item label="产品">
          <el-select v-model="lpForm.product_id" filterable style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="节拍(分钟)"><el-input-number v-model="lpForm.cycle_time_minutes" :min="0.01" :step="0.5" style="width:100%" /></el-form-item>
        <el-form-item label="准备时间(分)"><el-input-number v-model="lpForm.setup_time_minutes" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="单位成本"><el-input-number v-model="lpForm.cost_per_unit" :min="0" :step="0.1" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="lpDialog=false">取消</el-button>
        <el-button type="primary" @click="saveLp">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="coDialog" title="添加换型时间" width="380px">
      <el-form :model="coForm" label-width="90px">
        <el-form-item label="从产品">
          <el-select v-model="coForm.from_product_id" filterable style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="至产品">
          <el-select v-model="coForm.to_product_id" filterable style="width:100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="换型时间(分)"><el-input-number v-model="coForm.changeover_minutes" :min="0" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="coDialog=false">取消</el-button>
        <el-button type="primary" @click="saveCo">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productionApi, productsApi } from '../api'

const activeTab = ref('lines')
const lines = ref([])
const selectedLine = ref(null)
const lineProducts = ref([])
const calendar = ref([])
const changeovers = ref([])
const products = ref([])
const lineDialog = ref(false)
const lpDialog = ref(false)
const coDialog = ref(false)
const lineForm = ref({})
const lpForm = ref({})
const coForm = ref({})
const calRange = ref([])
const genShifts = ref(2)

async function loadLines() {
  const res = await productionApi.listLines()
  lines.value = res.data
}

async function selectLine(row) {
  selectedLine.value = row
  const [lp, cal, co] = await Promise.all([
    productionApi.lineProducts(row.id),
    productionApi.getCalendar(row.id),
    productionApi.listChangeovers(row.id),
  ])
  lineProducts.value = lp.data
  calendar.value = cal.data
  changeovers.value = co.data
}

function openLineDialog(row = null) {
  lineForm.value = row ? { ...row } : { code: '', name: '', shifts_per_day: 2, capacity_per_shift: 8, workers_per_shift: 10 }
  lineDialog.value = true
}

async function saveLine() {
  try {
    if (lineForm.value.id) {
      await productionApi.updateLine(lineForm.value.id, lineForm.value)
    } else {
      await productionApi.createLine(lineForm.value)
    }
    ElMessage.success('保存成功')
    lineDialog.value = false
    loadLines()
  } catch { ElMessage.error('保存失败') }
}

function openLpDialog() {
  lpForm.value = { product_id: null, cycle_time_minutes: 1, setup_time_minutes: 0, cost_per_unit: 0 }
  lpDialog.value = true
}

async function saveLp() {
  try {
    await productionApi.addLineProduct({ ...lpForm.value, line_id: selectedLine.value.id })
    ElMessage.success('绑定成功')
    lpDialog.value = false
    selectLine(selectedLine.value)
  } catch { ElMessage.error('绑定失败') }
}

async function deleteLp(id) {
  await ElMessageBox.confirm('确认删除?', '警告', { type: 'warning' })
  await productionApi.deleteLineProduct(id)
  selectLine(selectedLine.value)
}

async function generateCal() {
  if (!calRange.value?.length) return ElMessage.warning('请选择日期范围')
  await productionApi.generateCalendar(selectedLine.value.id, {
    start_date: calRange.value[0], end_date: calRange.value[1], shifts_per_day: genShifts.value
  })
  ElMessage.success('日历生成成功')
  selectLine(selectedLine.value)
}

function openCoDialog() {
  coForm.value = { from_product_id: null, to_product_id: null, changeover_minutes: 30 }
  coDialog.value = true
}

async function saveCo() {
  try {
    await productionApi.addChangeover({ ...coForm.value, line_id: selectedLine.value.id })
    ElMessage.success('添加成功')
    coDialog.value = false
    selectLine(selectedLine.value)
  } catch { ElMessage.error('添加失败') }
}

async function deleteCo(id) {
  await ElMessageBox.confirm('确认删除?', '警告', { type: 'warning' })
  await productionApi.deleteChangeover(id)
  selectLine(selectedLine.value)
}

onMounted(async () => {
  loadLines()
  const res = await productsApi.list()
  products.value = res.data
})
</script>
