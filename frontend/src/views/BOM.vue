<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>产品主数据</span>
              <el-button type="primary" size="small" icon="Plus" @click="openProductDialog()">新建产品</el-button>
            </div>
          </template>
          <el-input v-model="searchText" placeholder="搜索产品..." prefix-icon="Search" style="margin-bottom:12px" />
          <el-table :data="filteredProducts" @row-click="selectProduct" highlight-current-row size="small" max-height="500">
            <el-table-column prop="code" label="编码" width="100" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="product_type" label="类型" width="60">
              <template #default="{ row }">
                <el-tag :type="row.product_type === 'FG' ? 'primary' : row.product_type === 'SFG' ? 'warning' : 'info'" size="small">
                  {{ row.product_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lead_time_days" label="提前期(天)" width="90" align="right" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button text type="primary" size="small" @click.stop="openProductDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card v-if="selectedProduct">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>BOM - {{ selectedProduct.name }}</span>
              <el-button type="primary" size="small" icon="Plus" @click="openBomDialog()">添加BOM</el-button>
            </div>
          </template>
          <el-table :data="bomItems" size="small">
            <el-table-column label="子件编码" prop="child_product.code" width="100" />
            <el-table-column label="子件名称" prop="child_product.name" />
            <el-table-column label="用量" prop="quantity" width="80" align="right" />
            <el-table-column label="单位" prop="unit" width="60" />
            <el-table-column label="报废率" width="80" align="right">
              <template #default="{ row }">{{ (row.scrap_rate * 100).toFixed(1) }}%</template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button text type="danger" size="small" @click="deleteBomItem(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="bomTree" style="margin-top:20px">
            <el-divider>BOM树形结构</el-divider>
            <BomTreeNode :node="bomTree" />
          </div>
        </el-card>
        <el-card v-else>
          <el-empty description="请选择产品查看BOM" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Product Dialog -->
    <el-dialog v-model="productDialog" :title="productForm.id ? '编辑产品' : '新建产品'" width="480px">
      <el-form :model="productForm" label-width="100px">
        <el-form-item label="产品编码"><el-input v-model="productForm.code" :disabled="!!productForm.id" /></el-form-item>
        <el-form-item label="产品名称"><el-input v-model="productForm.name" /></el-form-item>
        <el-form-item label="产品类型">
          <el-select v-model="productForm.product_type" style="width:100%">
            <el-option label="成品 (FG)" value="FG" />
            <el-option label="半成品 (SFG)" value="SFG" />
            <el-option label="原材料 (RM)" value="RM" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位"><el-input v-model="productForm.unit" /></el-form-item>
        <el-form-item label="提前期(天)"><el-input-number v-model="productForm.lead_time_days" :min="0" :step="0.5" style="width:100%" /></el-form-item>
        <el-form-item label="安全库存"><el-input-number v-model="productForm.safety_stock" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="productForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productDialog=false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>

    <!-- BOM Dialog -->
    <el-dialog v-model="bomDialog" title="添加BOM子件" width="400px">
      <el-form :model="bomForm" label-width="80px">
        <el-form-item label="子件产品">
          <el-select v-model="bomForm.child_product_id" filterable style="width:100%">
            <el-option v-for="p in products.filter(p => p.id !== selectedProduct?.id)" :key="p.id"
              :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用量"><el-input-number v-model="bomForm.quantity" :min="0.001" :step="1" style="width:100%" /></el-form-item>
        <el-form-item label="报废率(%)"><el-input-number v-model="bomForm.scrap_rate_pct" :min="0" :max="100" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bomDialog=false">取消</el-button>
        <el-button type="primary" @click="saveBom">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { productsApi } from '../api'

// BOM Tree Node component
const BomTreeNode = {
  name: 'BomTreeNode',
  props: ['node'],
  template: `
    <div style="margin-left:16px">
      <div style="display:flex;align-items:center;gap:8px;padding:4px 0">
        <span style="color:#409eff">{{ node.product?.code }}</span>
        <span>{{ node.product?.name }}</span>
        <el-tag size="small" :type="node.product?.product_type === 'FG' ? 'primary' : node.product?.product_type === 'SFG' ? 'warning' : 'info'">
          {{ node.product?.product_type }}
        </el-tag>
        <span style="color:#666">× {{ node.quantity }}</span>
      </div>
      <div v-if="node.children?.length" style="border-left:2px solid #e4e7ed;margin-left:8px">
        <BomTreeNode v-for="child in node.children" :key="child.product?.id" :node="child" />
      </div>
    </div>
  `,
}

const products = ref([])
const selectedProduct = ref(null)
const bomItems = ref([])
const bomTree = ref(null)
const searchText = ref('')
const productDialog = ref(false)
const bomDialog = ref(false)
const productForm = ref({})
const bomForm = ref({})

const filteredProducts = computed(() =>
  products.value.filter(p =>
    p.name.includes(searchText.value) || p.code.includes(searchText.value)
  )
)

async function load() {
  const res = await productsApi.list()
  products.value = res.data
}

async function selectProduct(row) {
  selectedProduct.value = row
  const [bom, tree] = await Promise.all([
    productsApi.getBom(row.id),
    productsApi.getTree(row.id),
  ])
  bomItems.value = bom.data
  bomTree.value = tree.data
}

function openProductDialog(row = null) {
  productForm.value = row
    ? { ...row }
    : { code: '', name: '', product_type: 'FG', unit: 'PCS', lead_time_days: 1, safety_stock: 0, description: '' }
  productDialog.value = true
}

async function saveProduct() {
  try {
    if (productForm.value.id) {
      await productsApi.update(productForm.value.id, productForm.value)
    } else {
      await productsApi.create(productForm.value)
    }
    ElMessage.success('保存成功')
    productDialog.value = false
    load()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

function openBomDialog() {
  bomForm.value = { child_product_id: null, quantity: 1, scrap_rate_pct: 0 }
  bomDialog.value = true
}

async function saveBom() {
  try {
    await productsApi.addBomItem({
      parent_product_id: selectedProduct.value.id,
      child_product_id: bomForm.value.child_product_id,
      quantity: bomForm.value.quantity,
      scrap_rate: (bomForm.value.scrap_rate_pct || 0) / 100,
    })
    ElMessage.success('添加成功')
    bomDialog.value = false
    selectProduct(selectedProduct.value)
  } catch { ElMessage.error('添加失败') }
}

async function deleteBomItem(id) {
  await ElMessageBox.confirm('确认删除?', '警告', { type: 'warning' })
  await productsApi.deleteBomItem(id)
  ElMessage.success('已删除')
  selectProduct(selectedProduct.value)
}

onMounted(load)
</script>
