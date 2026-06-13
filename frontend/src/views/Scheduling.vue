<template>
  <div>
    <el-card style="margin-bottom:16px">
      <el-row :gutter="16" align="middle">
        <el-col :span="4">
          <el-select v-model="algorithm" placeholder="选择算法">
            <el-option label="EDD (最早交期)" value="EDD" />
            <el-option label="回溯+贪心" value="Backtracking" />
            <el-option label="线性优先级" value="Linear" />
            <el-option label="MIP整数规划" value="MIP" />
            <el-option label="模拟退火" value="SimulatedAnnealing" />
            <el-option label="蚁群算法" value="AntColony" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="objective" placeholder="优化目标">
            <el-option label="最高准时率" value="on_time" />
            <el-option label="最低成本" value="cost" />
            <el-option label="最短工期" value="makespan" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-input v-model="scheduleName" placeholder="排程方案名称" />
        </el-col>
        <el-col :span="3">
          <el-date-picker v-model="startDate" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" />
        </el-col>
        <el-col :span="3">
          <el-button type="primary" :loading="running" @click="runSchedule" icon="CaretRight">
            开始排程
          </el-button>
        </el-col>
        <el-col :span="3">
          <el-button type="warning" @click="compareDialog=true" icon="DataAnalysis">方案对比</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6" v-for="kpi in kpiList" :key="kpi.label">
        <el-card class="kpi-mini">
          <div class="kpi-val" :style="{ color: kpi.color }">{{ kpi.value }}</div>
          <div class="kpi-lbl">{{ kpi.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="tab">
      <el-tab-pane label="排程历史" name="history">
        <el-table :data="schedules" stripe size="small">
          <el-table-column prop="name" label="方案名称" />
          <el-table-column prop="algorithm" label="算法" width="150" />
          <el-table-column prop="on_time_rate" label="准时率%" width="90" align="right">
            <template #default="{ row }">
              <el-tag :type="row.on_time_rate >= 90 ? 'success' : row.on_time_rate >= 70 ? 'warning' : 'danger'" size="small">
                {{ row.on_time_rate }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_cost" label="总成本" width="100" align="right" />
          <el-table-column prop="utilization_rate" label="产能利用率%" width="110" align="right" />
          <el-table-column prop="makespan_days" label="工期(天)" width="90" align="right">
            <template #default="{ row }">{{ row.makespan_days?.toFixed(1) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : ''" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button text size="small" type="primary" @click="viewSchedule(row.id)">查看</el-button>
              <el-button text size="small" type="success" @click="approveSchedule(row.id)">激活</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="排程甘特图" name="gantt" v-if="currentSchedule">
        <el-card>
          <template #header><span>{{ currentSchedule.name }} - 排程甘特图</span></template>
          <div class="gantt-container">
            <div v-for="item in ganttItems" :key="item.id" class="gantt-row">
              <div class="gantt-label">{{ item.order_no || item.product_name }}</div>
              <div class="gantt-track">
                <div class="gantt-bar"
                  :style="{
                    left: item.leftPct + '%',
                    width: item.widthPct + '%',
                    background: item.is_on_time ? '#67c23a' : '#f56c6c'
                  }"
                  :title="`${item.start_datetime} → ${item.end_datetime} | ${item.line_name}`">
                  {{ item.product_name }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="排程明细" name="detail" v-if="currentSchedule">
        <el-table :data="scheduleItems" stripe size="small">
          <el-table-column prop="sequence" label="序号" width="60" />
          <el-table-column prop="order_no" label="订单号" width="120" />
          <el-table-column prop="product_code" label="产品编码" width="110" />
          <el-table-column prop="product_name" label="产品名称" />
          <el-table-column prop="line_name" label="生产线" width="100" />
          <el-table-column prop="planned_quantity" label="计划量" width="80" align="right" />
          <el-table-column prop="start_datetime" label="开始时间" width="150" />
          <el-table-column prop="end_datetime" label="结束时间" width="150" />
          <el-table-column prop="changeover_minutes" label="换型(分)" width="80" align="right" />
          <el-table-column prop="cost" label="成本" width="80" align="right">
            <template #default="{ row }">{{ row.cost?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="准时" width="70">
            <template #default="{ row }">
              <el-tag :type="row.is_on_time ? 'success' : 'danger'" size="small">
                {{ row.is_on_time ? '准时' : '延迟' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Compare Dialog -->
    <el-dialog v-model="compareDialog" title="排程方案对比" width="800px">
      <el-checkbox-group v-model="compareIds" style="margin-bottom:12px">
        <el-checkbox v-for="s in schedules" :key="s.id" :label="s.id">{{ s.name }} ({{ s.algorithm }})</el-checkbox>
      </el-checkbox-group>
      <el-button type="primary" @click="runCompare">对比</el-button>
      <el-table v-if="compareData.length" :data="compareData" style="margin-top:12px" border>
        <el-table-column prop="name" label="方案名称" />
        <el-table-column prop="algorithm" label="算法" width="140" />
        <el-table-column prop="on_time_rate" label="准时率%" align="right">
          <template #default="{ row }">
            <el-tag :type="row.on_time_rate === Math.max(...compareData.map(r => r.on_time_rate)) ? 'success' : ''">
              {{ row.on_time_rate }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_cost" label="总成本" align="right" />
        <el-table-column prop="utilization_rate" label="利用率%" align="right" />
        <el-table-column prop="makespan_days" label="工期(天)" align="right">
          <template #default="{ row }">{{ row.makespan_days?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column label="激活">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="approveSchedule(row.schedule_id)">激活</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulingApi } from '../api'

const algorithm = ref('EDD')
const objective = ref('on_time')
const scheduleName = ref('新排程方案')
const startDate = ref('')
const running = ref(false)
const schedules = ref([])
const currentSchedule = ref(null)
const scheduleItems = ref([])
const tab = ref('history')
const compareDialog = ref(false)
const compareIds = ref([])
const compareData = ref([])

const kpiList = computed(() => {
  if (!currentSchedule.value) return []
  const s = currentSchedule.value
  return [
    { label: '准时率', value: `${s.on_time_rate}%`, color: s.on_time_rate >= 90 ? '#67c23a' : '#f56c6c' },
    { label: '总成本', value: `¥${s.total_cost?.toFixed(0)}`, color: '#409eff' },
    { label: '产能利用率', value: `${s.utilization_rate}%`, color: '#e6a23c' },
    { label: '总工期(天)', value: s.makespan_days?.toFixed(1), color: '#909399' },
  ]
})

const ganttItems = computed(() => {
  if (!scheduleItems.value.length) return []
  const starts = scheduleItems.value.map(i => new Date(i.start_datetime).getTime())
  const ends = scheduleItems.value.map(i => new Date(i.end_datetime).getTime())
  const minT = Math.min(...starts)
  const maxT = Math.max(...ends)
  const span = maxT - minT || 1
  return scheduleItems.value.map(i => ({
    ...i,
    leftPct: ((new Date(i.start_datetime).getTime() - minT) / span) * 100,
    widthPct: Math.max(((new Date(i.end_datetime).getTime() - new Date(i.start_datetime).getTime()) / span) * 100, 1),
  }))
})

async function runSchedule() {
  running.value = true
  try {
    const res = await schedulingApi.run({
      algorithm: algorithm.value,
      name: scheduleName.value,
      objective: objective.value,
      start_date: startDate.value || undefined,
    })
    if (res.data.error) { ElMessage.error(res.data.error); return }
    ElMessage.success(`排程完成! 准时率: ${res.data.kpis?.on_time_rate}%`)
    loadSchedules()
    viewScheduleData(res.data)
  } catch (e) { ElMessage.error('排程失败: ' + (e.response?.data?.detail || e.message)) }
  finally { running.value = false }
}

function viewScheduleData(data) {
  currentSchedule.value = { id: data.schedule_id, name: scheduleName.value, ...data.kpis }
  scheduleItems.value = data.items || []
  tab.value = 'gantt'
}

async function viewSchedule(id) {
  const res = await schedulingApi.get(id)
  currentSchedule.value = res.data
  scheduleItems.value = res.data.items || []
  tab.value = 'detail'
}

async function approveSchedule(id) {
  await schedulingApi.approve(id)
  ElMessage.success('方案已激活')
  loadSchedules()
}

async function loadSchedules() {
  const res = await schedulingApi.list()
  schedules.value = res.data
}

async function runCompare() {
  if (compareIds.value.length < 2) return ElMessage.warning('请至少选择2个方案')
  const res = await schedulingApi.compare(compareIds.value)
  compareData.value = res.data
}

onMounted(loadSchedules)
</script>

<style scoped>
.kpi-mini { text-align: center; }
.kpi-val { font-size: 28px; font-weight: 700; }
.kpi-lbl { color: #666; font-size: 12px; margin-top: 4px; }
.gantt-container { overflow-x: auto; }
.gantt-row { display: flex; align-items: center; margin-bottom: 4px; min-height: 32px; }
.gantt-label { width: 160px; font-size: 12px; color: #303133; padding-right: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0; }
.gantt-track { flex: 1; height: 24px; background: #f5f7fa; position: relative; border-radius: 4px; min-width: 200px; }
.gantt-bar {
  position: absolute; height: 100%; border-radius: 4px; display: flex; align-items: center;
  padding: 0 4px; font-size: 11px; color: white; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; cursor: pointer; min-width: 2px; transition: opacity 0.2s;
}
.gantt-bar:hover { opacity: 0.85; }
</style>
