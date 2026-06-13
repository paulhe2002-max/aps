<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="24">
        <el-card>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-button type="primary" :loading="mrpLoading" @click="runMrp" icon="RefreshRight" size="large">
                运行MRP净需求计算
              </el-button>
            </el-col>
            <el-col :span="6">
              <el-date-picker v-model="rccpRange" type="daterange" value-format="YYYY-MM-DD"
                start-placeholder="RCCP开始" end-placeholder="RCCP结束" />
            </el-col>
            <el-col :span="4">
              <el-select v-model="bucketType">
                <el-option label="按周" value="week" />
                <el-option label="按月" value="month" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-button type="warning" :loading="rccpLoading" @click="runRccp" icon="DataAnalysis">
                运行RCCP粗产能
              </el-button>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="净需求明细" name="mrp">
        <el-card>
          <el-table :data="netRequirements" stripe size="small" v-loading="mrpLoading">
            <el-table-column prop="product_code" label="产品编码" width="110" />
            <el-table-column prop="product_name" label="产品名称" />
            <el-table-column label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_independent ? 'primary' : 'warning'" size="small">
                  {{ row.is_independent ? '独立需求' : '相关需求' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="gross_requirement" label="毛需求" width="90" align="right" />
            <el-table-column prop="actual_stock" label="实际库存" width="90" align="right" />
            <el-table-column prop="in_transit" label="在途" width="70" align="right" />
            <el-table-column prop="wip" label="在制" width="70" align="right" />
            <el-table-column prop="safety_stock" label="安全库存" width="90" align="right" />
            <el-table-column prop="net_requirement" label="净需求" width="90" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.net_requirement > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
                  {{ row.net_requirement }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="交期" width="110" />
            <el-table-column prop="latest_start_date" label="最晚开始" width="110">
              <template #default="{ row }">
                <span :style="{ color: isLate(row.latest_start_date) ? '#f56c6c' : '' }">
                  {{ row.latest_start_date }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="RCCP产能分析" name="rccp">
        <el-card>
          <el-table :data="rccpResults" stripe size="small" v-loading="rccpLoading">
            <el-table-column prop="line_name" label="产线" width="120" />
            <el-table-column prop="period_start" label="开始日期" width="110" />
            <el-table-column prop="period_end" label="结束日期" width="110" />
            <el-table-column prop="required_capacity_hours" label="需求产能(时)" width="120" align="right" />
            <el-table-column prop="available_capacity_hours" label="可用产能(时)" width="120" align="right" />
            <el-table-column prop="adjustment_hours" label="调整(时)" width="90" align="right">
              <template #default="{ row }">
                <el-input-number v-model="row.adjustment_hours" size="small" :step="1"
                  style="width:80px" @change="adjustCapacity(row)" />
              </template>
            </el-table-column>
            <el-table-column prop="utilization_rate" label="利用率%" width="90" align="right">
              <template #default="{ row }">
                <el-progress :percentage="Math.min(row.utilization_rate, 100)"
                  :status="row.utilization_rate > 100 ? 'exception' : row.utilization_rate > 85 ? 'warning' : 'success'"
                  :stroke-width="10" :text-inside="false" />
              </template>
            </el-table-column>
            <el-table-column label="超载" width="70">
              <template #default="{ row }">
                <el-tag v-if="row.is_overloaded" type="danger" size="small">超载</el-tag>
                <el-tag v-else type="success" size="small">正常</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { planningApi } from '../api'

const activeTab = ref('mrp')
const mrpLoading = ref(false)
const rccpLoading = ref(false)
const netRequirements = ref([])
const rccpResults = ref([])
const rccpRange = ref([])
const bucketType = ref('week')

function isLate(d) {
  return d && new Date(d) < new Date()
}

async function runMrp() {
  mrpLoading.value = true
  try {
    const res = await planningApi.runMrp()
    netRequirements.value = res.data.results
    ElMessage.success(`MRP计算完成: ${res.data.count}条需求`)
  } catch { ElMessage.error('MRP计算失败') } finally { mrpLoading.value = false }
}

async function loadMrp() {
  const res = await planningApi.getNetRequirements()
  netRequirements.value = res.data
}

async function runRccp() {
  if (!rccpRange.value?.length) return ElMessage.warning('请选择RCCP日期范围')
  rccpLoading.value = true
  try {
    const res = await planningApi.runRccp({ start_date: rccpRange.value[0], end_date: rccpRange.value[1], bucket_type: bucketType.value })
    rccpResults.value = res.data.results
    ElMessage.success(`RCCP计算完成: ${res.data.count}条记录`)
  } catch { ElMessage.error('RCCP计算失败') } finally { rccpLoading.value = false }
}

async function loadRccp() {
  const res = await planningApi.getRccpResults()
  rccpResults.value = res.data
}

async function adjustCapacity(row) {
  await planningApi.adjustRccp(row.id, row.adjustment_hours)
  ElMessage.success('产能调整已保存')
}

onMounted(() => { loadMrp(); loadRccp() })
</script>
