<template>
  <div>
    <el-tabs v-model="tab">
      <el-tab-pane label="库存健康" name="inventory">
        <el-card>
          <el-row :gutter="12" style="margin-bottom:12px">
            <el-col :span="4">
              <el-statistic title="总SKU" :value="inventoryData.length" />
            </el-col>
            <el-col :span="4">
              <el-statistic title="库存充足" :value="inventoryData.filter(r=>r.status==='OK').length"
                :value-style="{ color: '#67c23a' }" />
            </el-col>
            <el-col :span="4">
              <el-statistic title="库存偏低" :value="inventoryData.filter(r=>r.status==='LOW').length"
                :value-style="{ color: '#e6a23c' }" />
            </el-col>
            <el-col :span="4">
              <el-statistic title="缺货" :value="inventoryData.filter(r=>r.status==='STOCKOUT').length"
                :value-style="{ color: '#f56c6c' }" />
            </el-col>
          </el-row>
          <el-table :data="inventoryData" stripe size="small">
            <el-table-column prop="product_code" label="产品编码" width="110" />
            <el-table-column prop="product_name" label="产品名称" />
            <el-table-column prop="actual_stock" label="实际库存" align="right" width="90" />
            <el-table-column prop="safety_stock" label="安全库存" align="right" width="90" />
            <el-table-column prop="in_transit" label="在途" align="right" width="70" />
            <el-table-column prop="wip" label="在制" align="right" width="70" />
            <el-table-column label="覆盖率" width="80" align="right">
              <template #default="{ row }">{{ row.coverage_ratio !== null ? `${(row.coverage_ratio * 100).toFixed(0)}%` : 'N/A' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'OK' ? 'success' : row.status === 'LOW' ? 'warning' : 'danger'" size="small">
                  {{ { OK: '充足', LOW: '偏低', STOCKOUT: '缺货' }[row.status] || row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="订单履行" name="fulfillment">
        <el-card>
          <el-table :data="fulfillmentData" stripe size="small">
            <el-table-column prop="schedule_name" label="排程方案" />
            <el-table-column prop="algorithm" label="算法" width="150" />
            <el-table-column prop="total_jobs" label="总工单" width="80" align="right" />
            <el-table-column prop="on_time_jobs" label="准时" width="70" align="right" />
            <el-table-column prop="on_time_rate" label="准时率%" width="80" align="right">
              <template #default="{ row }">
                <el-tag :type="row.on_time_rate >= 90 ? 'success' : row.on_time_rate >= 70 ? 'warning' : 'danger'" size="small">
                  {{ row.on_time_rate }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_cost" label="总成本" width="100" align="right">
              <template #default="{ row }">{{ row.total_cost?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="utilization_rate" label="利用率%" width="90" align="right" />
            <el-table-column prop="makespan_days" label="工期(天)" width="80" align="right">
              <template #default="{ row }">{{ row.makespan_days?.toFixed(1) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : ''" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="产能利用" name="capacity">
        <el-card>
          <el-table :data="capacityData" stripe size="small">
            <el-table-column prop="line_name" label="产线" width="120" />
            <el-table-column prop="period" label="周期开始" width="110" />
            <el-table-column prop="period_end" label="周期结束" width="110" />
            <el-table-column prop="required_hours" label="需求工时" width="100" align="right" />
            <el-table-column prop="available_hours" label="可用工时" width="100" align="right" />
            <el-table-column label="利用率" width="200">
              <template #default="{ row }">
                <el-progress :percentage="Math.min(row.utilization_pct, 100)"
                  :status="row.utilization_pct > 100 ? 'exception' : row.utilization_pct > 85 ? 'warning' : ''"
                  :stroke-width="12" />
              </template>
            </el-table-column>
            <el-table-column prop="utilization_pct" label="%" width="60" align="right">
              <template #default="{ row }">
                <span :style="{ color: row.is_overloaded ? '#f56c6c' : '' }">{{ row.utilization_pct }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="在制品分析" name="wip">
        <el-card>
          <el-table :data="wipData" stripe size="small">
            <el-table-column prop="product_code" label="产品编码" width="120" />
            <el-table-column prop="product_name" label="产品名称" />
            <el-table-column prop="wip_quantity" label="在制数量" align="right" width="100" />
            <el-table-column prop="actual_stock" label="成品库存" align="right" width="100" />
            <el-table-column prop="in_transit" label="在途数量" align="right" width="100" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- Fixed action buttons -->
    <div style="position:fixed;bottom:30px;right:30px;display:flex;gap:10px;flex-direction:column;align-items:flex-end">
      <el-button type="success" icon="Download" @click="downloadUserManual" :loading="dlManual">
        下载用户操作手册
      </el-button>
      <el-button type="warning" icon="Download" @click="downloadAlgoDemo" :loading="dlAlgo">
        下载算法演示手册
      </el-button>
      <el-button type="primary" @click="loadAll" icon="Refresh">
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api'
import axios from 'axios'

const tab = ref('inventory')
const inventoryData = ref([])
const fulfillmentData = ref([])
const capacityData = ref([])
const wipData = ref([])

async function loadAll() {
  try {
    const [inv, ful, cap, wip] = await Promise.all([
      reportsApi.inventoryHealth(),
      reportsApi.orderFulfillment(),
      reportsApi.capacityUtilization(),
      reportsApi.wipAnalysis(),
    ])
    inventoryData.value = inv.data
    fulfillmentData.value = ful.data
    capacityData.value = cap.data
    wipData.value = wip.data
  } catch {}
}

onMounted(loadAll)

const dlManual = ref(false)
const dlAlgo   = ref(false)

async function downloadFile(url, filename, loadingRef) {
  loadingRef.value = true
  try {
    const token = localStorage.getItem('token')
    const resp = await axios.get(url, {
      responseType: 'blob',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const href = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = href
    a.download = filename
    a.click()
    URL.revokeObjectURL(href)
  } finally {
    loadingRef.value = false
  }
}

function downloadUserManual() {
  downloadFile('/api/export/user-manual', 'APS_用户操作手册.xlsx', dlManual)
}
function downloadAlgoDemo() {
  downloadFile('/api/export/algorithm-demo', 'APS_算法逐步演示.xlsx', dlAlgo)
}
</script>
