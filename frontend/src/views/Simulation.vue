<template>
  <div>
    <el-card style="margin-bottom:16px">
      <template #header><span>算法演示 - 逐步展示排程算法中间结果</span></template>
      <el-row :gutter="16" align="middle">
        <el-col :span="5">
          <el-select v-model="algorithm" placeholder="选择算法" style="width:100%">
            <el-option label="EDD (最早交期优先)" value="EDD" />
            <el-option label="回溯+贪心算法" value="Backtracking" />
            <el-option label="线性优先级排序" value="Linear" />
            <el-option label="MIP整数规划" value="MIP" />
            <el-option label="模拟退火 (SA)" value="SimulatedAnnealing" />
            <el-option label="蚁群优化 (ACO)" value="AntColony" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" :loading="loading" @click="startSimulation">开始演示</el-button>
        </el-col>
        <el-col :span="3" v-if="steps.length">
          <el-button :disabled="currentStep <= 0" @click="prevStep">上一步</el-button>
        </el-col>
        <el-col :span="3" v-if="steps.length">
          <el-button type="primary" :disabled="currentStep >= steps.length - 1" @click="nextStep">下一步</el-button>
        </el-col>
        <el-col :span="3" v-if="steps.length">
          <el-button type="success" :disabled="autoRunning" @click="autoPlay">自动播放</el-button>
        </el-col>
        <el-col :span="3" v-if="autoRunning">
          <el-button type="danger" @click="stopAuto">停止</el-button>
        </el-col>
      </el-row>

      <el-progress v-if="steps.length" :percentage="Math.round((currentStep + 1) / steps.length * 100)"
        style="margin-top:16px" :format="(p) => `步骤 ${currentStep + 1}/${steps.length}`" />
    </el-card>

    <el-row :gutter="16" v-if="steps.length">
      <el-col :span="14">
        <el-card style="min-height:400px">
          <template #header>
            <span>步骤 {{ currentStep + 1 }}: {{ currentStepData?.action }}</span>
          </template>
          <div v-if="currentStepData">
            <el-alert v-if="typeof currentStepData.detail === 'string'"
              :title="currentStepData.detail" type="info" :closable="false" style="margin-bottom:12px" />

            <div v-else-if="Array.isArray(currentStepData.detail)">
              <el-table v-if="currentStepData.detail[0]?.order_no !== undefined" :data="currentStepData.detail" size="small">
                <el-table-column prop="order_no" label="订单号" />
                <el-table-column prop="due_date" label="交期" />
                <el-table-column prop="quantity" label="数量" align="right" />
              </el-table>
              <el-table v-else-if="currentStepData.detail[0]?.iteration !== undefined" :data="currentStepData.detail.slice(-20)" size="small">
                <el-table-column prop="iteration" label="迭代" width="80" />
                <el-table-column prop="temperature" label="温度/信息素" />
                <el-table-column prop="score" label="当前分数" align="right" />
                <el-table-column prop="best" label="最优分数" align="right" />
              </el-table>
              <el-table v-else-if="currentStepData.detail[0]?.score !== undefined" :data="currentStepData.detail" size="small">
                <el-table-column prop="order_no" label="订单" />
                <el-table-column prop="score" label="优先级分数" align="right" />
                <el-table-column prop="slack_hours" label="松弛时间(时)" align="right" />
              </el-table>
              <pre v-else style="font-size:12px;background:#f5f7fa;padding:12px;border-radius:4px;overflow:auto">{{ JSON.stringify(currentStepData.detail, null, 2) }}</pre>
            </div>

            <div v-else-if="typeof currentStepData.detail === 'object' && currentStepData.detail !== null">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item v-for="(v, k) in currentStepData.detail" :key="k" :label="k">
                  {{ typeof v === 'number' ? v.toFixed(2) : v }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card style="min-height:400px">
          <template #header><span>步骤导航</span></template>
          <div class="step-list">
            <div v-for="(s, i) in steps" :key="i"
              :class="['step-item', i === currentStep ? 'active' : '', i < currentStep ? 'done' : '']"
              @click="currentStep = i">
              <span class="step-no">{{ i + 1 }}</span>
              <span class="step-action">{{ s.action }}</span>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top:16px" v-if="kpis">
          <template #header><span>最终KPI结果</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="准时率">{{ kpis.on_time_rate }}%</el-descriptions-item>
            <el-descriptions-item label="准时订单">{{ kpis.on_time_jobs }}/{{ kpis.total_jobs }}</el-descriptions-item>
            <el-descriptions-item label="总成本">{{ kpis.total_cost?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="产能利用率">{{ kpis.utilization_rate }}%</el-descriptions-item>
            <el-descriptions-item label="总工期(小时)">{{ kpis.makespan_hours?.toFixed(1) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="!steps.length && !loading" style="margin-top:16px">
      <el-empty description="选择算法后点击[开始演示]查看算法逐步执行过程">
        <template #extra>
          <div class="algo-info">
            <el-row :gutter="12">
              <el-col :span="8" v-for="algo in algoDescriptions" :key="algo.name">
                <el-card shadow="never" class="algo-card">
                  <div class="algo-name">{{ algo.name }}</div>
                  <div class="algo-desc">{{ algo.desc }}</div>
                  <el-tag size="small" :type="algo.tagType">{{ algo.complexity }}</el-tag>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulingApi } from '../api'

const algorithm = ref('EDD')
const loading = ref(false)
const steps = ref([])
const kpis = ref(null)
const currentStep = ref(0)
const autoRunning = ref(false)
let autoTimer = null

const currentStepData = computed(() => steps.value[currentStep.value] || null)

const algoDescriptions = [
  { name: 'EDD - 最早交期', desc: '按交货期从早到晚排序，简单高效，适合追求准时率的场景', complexity: 'O(n log n)', tagType: 'success' },
  { name: '回溯+贪心', desc: '在贪心基础上进行多次随机调整，寻找更优解', complexity: 'O(n²)', tagType: 'primary' },
  { name: '线性优先级', desc: '基于松弛时间和优先级综合评分排序', complexity: 'O(n log n)', tagType: 'success' },
  { name: 'MIP整数规划', desc: '建立混合整数规划模型，数学最优但计算量大', complexity: 'NP-Hard', tagType: 'warning' },
  { name: '模拟退火', desc: '模拟金属退火过程，可跳出局部最优解', complexity: 'O(n·T)', tagType: 'warning' },
  { name: '蚁群优化', desc: '模拟蚂蚁觅食行为，适合复杂组合优化问题', complexity: 'O(m·n²)', tagType: 'danger' },
]

async function startSimulation() {
  loading.value = true
  steps.value = []
  kpis.value = null
  try {
    const res = await schedulingApi.simulate(algorithm.value)
    if (res.data.error) { ElMessage.error(res.data.error); return }
    steps.value = res.data.steps
    kpis.value = res.data.kpis
    currentStep.value = 0
    ElMessage.success(`算法演示就绪: ${res.data.total_steps}个步骤`)
  } catch (e) { ElMessage.error('演示失败: ' + (e.response?.data?.detail || e.message)) }
  finally { loading.value = false }
}

function prevStep() {
  if (currentStep.value > 0) currentStep.value--
}

function nextStep() {
  if (currentStep.value < steps.value.length - 1) currentStep.value++
}

function autoPlay() {
  autoRunning.value = true
  autoTimer = setInterval(() => {
    if (currentStep.value < steps.value.length - 1) {
      currentStep.value++
    } else {
      stopAuto()
    }
  }, 800)
}

function stopAuto() {
  clearInterval(autoTimer)
  autoRunning.value = false
}
</script>

<style scoped>
.step-list { max-height: 320px; overflow-y: auto; }
.step-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  cursor: pointer; border-radius: 6px; margin-bottom: 4px;
  transition: background 0.2s;
}
.step-item:hover { background: #f5f7fa; }
.step-item.active { background: #409eff; color: white; }
.step-item.done { color: #67c23a; }
.step-no {
  width: 24px; height: 24px; border-radius: 50%; background: rgba(0,0,0,0.1);
  display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0;
}
.step-action { font-size: 13px; }
.algo-info { margin-top: 16px; }
.algo-card { margin-bottom: 0; }
.algo-name { font-weight: 600; margin-bottom: 6px; color: #303133; }
.algo-desc { font-size: 12px; color: #666; margin-bottom: 8px; line-height: 1.4; }
</style>
