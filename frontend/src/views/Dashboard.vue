<template>
  <div>
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6" v-for="kpi in kpiCards" :key="kpi.label">
        <el-card class="kpi-card" :style="{ borderTop: `4px solid ${kpi.color}` }">
          <div class="kpi-content">
            <div class="kpi-value" :style="{ color: kpi.color }">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
          <el-icon class="kpi-icon" :style="{ color: kpi.color }"><component :is="kpi.icon" /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card title="库存健康状况">
          <template #header><span>库存健康状况</span></template>
          <el-table :data="inventoryHealth.slice(0,8)" size="small" max-height="300">
            <el-table-column prop="product_code" label="产品编码" width="100" />
            <el-table-column prop="product_name" label="产品名称" />
            <el-table-column prop="actual_stock" label="实际库存" width="90" align="right" />
            <el-table-column prop="safety_stock" label="安全库存" width="90" align="right" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'OK' ? 'success' : row.status === 'LOW' ? 'warning' : 'danger'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>近期排程绩效</span></template>
          <el-table :data="fulfillment" size="small" max-height="300">
            <el-table-column prop="schedule_name" label="排程名称" />
            <el-table-column prop="algorithm" label="算法" width="120" />
            <el-table-column prop="on_time_rate" label="准时率%" width="80" align="right">
              <template #default="{ row }">
                <el-tag :type="row.on_time_rate >= 90 ? 'success' : row.on_time_rate >= 70 ? 'warning' : 'danger'" size="small">
                  {{ row.on_time_rate }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : ''" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api'

const kpiCards = ref([])
const inventoryHealth = ref([])
const fulfillment = ref([])

async function load() {
  try {
    const [d, inv, ful] = await Promise.all([
      reportsApi.dashboard(),
      reportsApi.inventoryHealth(),
      reportsApi.orderFulfillment(),
    ])
    const data = d.data
    kpiCards.value = [
      { label: '待处理订单', value: data.open_orders, color: '#409eff', icon: 'Document' },
      { label: '逾期订单', value: data.overdue_orders, color: '#f56c6c', icon: 'Warning' },
      { label: '净需求条目', value: data.pending_net_requirements, color: '#e6a23c', icon: 'List' },
      { label: '产能超载期', value: data.overloaded_capacity_periods, color: '#f56c6c', icon: 'TrendCharts' },
      { label: '产品总数', value: data.total_products, color: '#67c23a', icon: 'Grid' },
      { label: '成品数量', value: data.fg_products, color: '#909399', icon: 'Box' },
      { label: '活动排程准时率', value: `${data.active_schedule_on_time_rate}%`, color: '#409eff', icon: 'Timer' },
      { label: '生产线数量', value: data.total_production_lines, color: '#67c23a', icon: 'Setting' },
    ]
    inventoryHealth.value = inv.data
    fulfillment.value = ful.data
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.kpi-row { margin-bottom: 8px; }
.kpi-card { position: relative; overflow: hidden; }
.kpi-content { z-index: 1; }
.kpi-value { font-size: 32px; font-weight: 700; line-height: 1; }
.kpi-label { color: #666; font-size: 13px; margin-top: 8px; }
.kpi-icon { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); font-size: 40px; opacity: 0.15; }
</style>
