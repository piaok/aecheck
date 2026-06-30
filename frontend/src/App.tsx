import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'

interface ExtractedStandard {
  id: number
  standard_number: string
  standard_name: string
}

interface CheckResult {
  id: number
  input_number: string
  input_name: string
  matched_number: string | null
  matched_name: string | null
  status: string
  matched_percentage: number
  message: string
}

interface Standard {
  id: number
  standard_number: string
  standard_name: string
  status: string
  release_date: string | null
  implement_date: string | null
  abolish_date: string | null
  replace_by: string | null
  source: string | null
  created_at: string | null
  updated_at: string | null
}

interface StandardForm {
  standard_number: string
  standard_name: string
  status: string
  release_date: string
  implement_date: string
  abolish_date: string
  replace_by: string
  source: string
}

interface UpdateSuggestion {
  action: 'update' | 'create'
  id?: number
  changes?: string[]
  data: {
    standard_number: string
    standard_name: string
    status: string
    source: string
    replace_by: string
  }
}

const STORAGE_KEY = 'aecheck_state'

function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load state from localStorage:', e)
  }
  return null
}

function saveState(state: any) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.error('Failed to save state to localStorage:', e)
  }
}

function App() {
  const savedState = loadState()

  const [activeTab, setActiveTab] = useState<'validate' | 'database' | 'settings'>('validate')
  const [text, setText] = useState(savedState?.text || '')
  const [extractedStandards, setExtractedStandards] = useState<ExtractedStandard[]>(savedState?.extractedStandards || [])
  const [showExtracted, setShowExtracted] = useState(savedState?.showExtracted || false)
  const [results, setResults] = useState<CheckResult[]>(savedState?.results || [])
  const [logs, setLogs] = useState<string[]>(savedState?.logs || [])
  const [loading, setLoading] = useState(false)
  const [extractLoading, setExtractLoading] = useState(false)
  const [error, setError] = useState('')
  const [online, setOnline] = useState(savedState?.online || false)
  const [updateSuggestions, setUpdateSuggestions] = useState<UpdateSuggestion[]>([])

  // AI配置状态
  const [aiBaseUrl, setAiBaseUrl] = useState('')
  const [aiToken, setAiToken] = useState('')
  const [aiModel, setAiModel] = useState('gpt-3.5-turbo')
  const [aiHasToken, setAiHasToken] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResults, setAiResults] = useState<any[]>([])

  const [standards, setStandards] = useState<Standard[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [dbLoading, setDbLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingStandard, setEditingStandard] = useState<Standard | null>(null)
  const [formData, setFormData] = useState<StandardForm>({
    standard_number: '',
    standard_name: '',
    status: '现行',
    release_date: '',
    implement_date: '',
    abolish_date: '',
    replace_by: '',
    source: ''
  })

  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const stateToSave = {
      text,
      extractedStandards,
      showExtracted,
      results,
      logs,
      online
    }
    saveState(stateToSave)
  }, [text, extractedStandards, showExtracted, results, logs, online])

  const scrollToLogsBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToLogsBottom()
  }, [logs])

  const handleExtract = async () => {
    if (!text.trim()) {
      setError('请输入要校验的规范内容')
      return
    }

    setExtractLoading(true)
    setError('')
    setExtractedStandards([])
    setShowExtracted(false)
    setResults([])
    setLogs([])

    try {
      const response = await axios.post('/api/extract', { text })
      const extracted = response.data.extracted
      setExtractedStandards(extracted)
      setShowExtracted(true)
      setLogs([`🔍 解析输入文本，识别到 ${extracted.length} 条规范`])
    } catch (err) {
      setError('文本解析失败，请检查输入内容')
      setLogs(['❌ 文本解析失败'])
      console.error(err)
    } finally {
      setExtractLoading(false)
    }
  }

  const handleValidate = async () => {
    if (!extractedStandards.length) {
      setError('请先提取结构化文本')
      return
    }

    setLoading(true)
    setError('')
    setResults([])
    setUpdateSuggestions([])

    try {
      const response = await axios.post('/api/validate', { text, online })
      setResults(response.data.results)
      setLogs(response.data.logs || [])
      setUpdateSuggestions(response.data.update_suggestions || [])
    } catch (err) {
      setError('校验失败，请稍后重试')
      setLogs(['❌ 校验失败'])
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmUpdates = async () => {
    if (!updateSuggestions.length) return

    try {
      const response = await axios.post('/api/standards/batch-update', updateSuggestions)
      const results = response.data.results
      let successCount = 0
      let failCount = 0

      results.forEach((r: any) => {
        if (r.success) successCount++
        else failCount++
      })

      setLogs(prev => [...prev, `📥 数据库更新完成: ${successCount} 成功, ${failCount} 失败`])
      setUpdateSuggestions([])
      handleReset()
    } catch (err) {
      console.error('Batch update failed:', err)
      setLogs(prev => [...prev, '❌ 数据库更新失败'])
    }
  }

  const handleReset = () => {
    setExtractedStandards([])
    setShowExtracted(false)
    setResults([])
    setLogs([])
    setError('')
  }

  const getStatusColor = (status: string) => {
    if (status === '正确') return 'bg-green-100 text-green-800 border-green-300'
    if (status === '规范已过期') return 'bg-red-100 text-red-800 border-red-300'
    if (status === '规范名称错误') return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    if (status === '规范标准号错误') return 'bg-orange-100 text-orange-800 border-orange-300'
    if (status === '现行') return 'bg-green-100 text-green-800 border-green-300'
    if (status === '废止') return 'bg-red-100 text-red-800 border-red-300'
    return 'bg-gray-100 text-gray-800 border-gray-300'
  }

  const fetchStandards = async (page = currentPage) => {
    setDbLoading(true)
    try {
      const skip = (page - 1) * pageSize
      const params: any = { skip, limit: pageSize }
      if (searchKeyword) params.keyword = searchKeyword

      const response = await axios.get('/api/standards', { params })
      setStandards(response.data.items)
      setTotalCount(response.data.total)
      setCurrentPage(page)
    } catch (err) {
      console.error('获取标准列表失败', err)
    } finally {
      setDbLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'database') {
      fetchStandards(1)
    }
    if (activeTab === 'settings') {
      fetch('/api/ai/config').then(r => r.json()).then(d => {
        setAiBaseUrl(d.base_url || '')
        setAiHasToken(d.has_token)
        setAiModel(d.model || 'gpt-3.5-turbo')
      }).catch(() => {})
    }
  }, [activeTab])

  const handleSaveAIConfig = async () => {
    try {
      const resp = await fetch('/api/ai/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_url: aiBaseUrl, token: aiToken, model: aiModel }),
      })
      if (resp.ok) {
        setAiHasToken(true)
        alert('AI配置已保存')
      } else {
        const data = await resp.json()
        alert('保存失败: ' + (data.detail || '未知错误'))
      }
    } catch (e) {
      alert('保存失败，请检查网络连接')
    }
  }

  const handleAIValidate = async () => {
    if (!showExtracted || extractedStandards.length === 0) {
      alert('请先解析文本')
      return
    }
    setAiLoading(true)
    setAiResults([])
    setLogs(prev => [...prev, '🤖 开始AI大模型校验...'])
    try {
      const resp = await fetch('/api/ai/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          standards: extractedStandards.map(s => ({ number: s.standard_number, name: s.standard_name })),
        }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        throw new Error(data.detail || 'AI校验失败')
      }
      setAiResults(data.results || [])
      setLogs(prev => [...prev, `✅ AI校验完成，共处理 ${(data.results || []).length} 条规范`])
    } catch (e: any) {
      setLogs(prev => [...prev, `❌ AI校验失败: ${e.message}`])
    } finally {
      setAiLoading(false)
    }
  }

  const totalPages = Math.ceil(totalCount / pageSize)

  const handleAddStandard = () => {
    setEditingStandard(null)
    setFormData({
      standard_number: '',
      standard_name: '',
      status: '现行',
      release_date: '',
      implement_date: '',
      abolish_date: '',
      replace_by: '',
      source: ''
    })
    setShowModal(true)
  }

  const handleEditStandard = (standard: Standard) => {
    setEditingStandard(standard)
    setFormData({
      standard_number: standard.standard_number,
      standard_name: standard.standard_name,
      status: standard.status,
      release_date: standard.release_date || '',
      implement_date: standard.implement_date || '',
      abolish_date: standard.abolish_date || '',
      replace_by: standard.replace_by || '',
      source: standard.source || ''
    })
    setShowModal(true)
  }

  const handleSaveStandard = async () => {
    try {
      if (editingStandard) {
        await axios.put(`/api/standards/${editingStandard.id}`, formData)
      } else {
        await axios.post('/api/standards', formData)
      }
      setShowModal(false)
      fetchStandards(currentPage)
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || '保存失败'
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }

  const handleDeleteStandard = async (id: number) => {
    if (confirm('确定要删除这个标准吗？')) {
      try {
        await axios.delete(`/api/standards/${id}`)
        fetchStandards(currentPage)
      } catch (err: any) {
        const msg = err.response?.data?.detail || err.message || '删除失败'
        alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
      }
    }
  }

  const handleSearch = () => {
    setCurrentPage(1)
    fetchStandards(1)
  }

  const handleClearSearch = () => {
    setSearchKeyword('')
    setCurrentPage(1)
    fetchStandards(1)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            建筑结构规范校验工具
          </h1>
          <p className="text-gray-600">
            输入非结构化文本，自动提取并校验建筑规范标准
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('validate')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === 'validate'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              规范校验
            </button>
            <button
              onClick={() => setActiveTab('database')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === 'database'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              数据库管理 ({totalCount})
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                activeTab === 'settings'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              设置
            </button>
          </div>

          {activeTab === 'validate' && (
            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                请输入要校验的规范内容
              </label>
              <textarea
                value={text}
                onChange={(e) => { setText(e.target.value); handleReset(); }}
                placeholder={`示例：\n《混凝土结构设计规范》（GB 50010-2010）\n《建筑抗震设计规范》（GB 50011-2010）\n支持多行输入，每行一条规范`}
                className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm"
              />
              <div className="flex justify-between items-center mt-4">
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500">
                    支持识别：GB、JGJ、GBJ、CECS、DB等标准编号
                  </span>
                  <label className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={online}
                      onChange={(e) => setOnline(e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    在线查询（联网校验）
                  </label>
                </div>
                <div className="flex gap-2">
                  {showExtracted && (
                    <button
                      onClick={handleReset}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
                    >
                      重置
                    </button>
                  )}
                  <button
                    onClick={handleExtract}
                    disabled={extractLoading || showExtracted}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {extractLoading ? '解析中...' : '解析文本'}
                  </button>
                  {showExtracted && (
                    <button
                      onClick={handleValidate}
                      disabled={loading}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors font-medium"
                    >
                      {loading ? '校验中...' : '开始校验'}
                    </button>
                  )}
                  {showExtracted && aiHasToken && (
                    <button
                      onClick={handleAIValidate}
                      disabled={aiLoading}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-purple-400 disabled:cursor-not-allowed transition-colors font-medium"
                    >
                      {aiLoading ? 'AI校验中...' : 'AI校验'}
                    </button>
                  )}
                </div>
              </div>
              {error && (
                <div className="mt-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              {showExtracted && extractedStandards.length > 0 && (
                <div className="mt-6">
                  <div className="px-4 py-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h2 className="text-lg font-semibold text-gray-900">步骤1：提取的结构化文本</h2>
                    <p className="text-xs text-gray-500 mt-1">请确认提取结果是否正确，然后点击"开始校验"</p>
                  </div>
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">序号</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标准号</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">规范名称</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {extractedStandards.map((item) => (
                          <tr key={item.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">{item.id}</td>
                            <td className="px-4 py-3 text-sm text-gray-900 font-medium">{item.standard_number}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {item.standard_name || <span className="text-red-500">（未识别）</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {logs.length > 0 && (
                <div className="mt-4 bg-gray-900 rounded-lg p-4 overflow-hidden">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-semibold text-white">执行日志</h3>
                    <button
                      onClick={() => setLogs([])}
                      className="text-xs text-gray-400 hover:text-white"
                    >
                      清空日志
                    </button>
                  </div>
                  <div className="max-h-48 overflow-y-auto text-xs font-mono">
                    {logs.map((log, idx) => (
                      <div key={idx} className="text-gray-300 py-0.5">{log}</div>
                    ))}
                    <div ref={logsEndRef} />
                  </div>
                </div>
              )}

              {results.length > 0 && (
                <div className="mt-6">
                  <div className="px-4 py-3 bg-green-50 border border-green-200 rounded-lg">
                    <h2 className="text-lg font-semibold text-gray-900">步骤2：校验结果</h2>
                  </div>
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">序号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">输入标准号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">输入名称</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">匹配标准号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">匹配名称</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">说明</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {results.map((result) => (
                          <tr key={result.id} className="hover:bg-gray-50">
                            <td className="px-3 py-3 text-sm text-gray-900">{result.id}</td>
                            <td className="px-3 py-3 text-sm text-gray-900 font-medium">{result.input_number}</td>
                            <td className="px-3 py-3 text-sm text-gray-600">{result.input_name || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-900">{result.matched_number || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-600">{result.matched_name || '-'}</td>
                            <td className="px-3 py-3">
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(result.status)}`}>
                                {result.status}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-sm text-gray-600">{result.message}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {updateSuggestions.length > 0 && (
                <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold text-amber-900">数据库更新建议</h3>
                    <span className="text-sm text-amber-700">共 {updateSuggestions.length} 项建议</span>
                  </div>
                  <div className="space-y-3 mb-4">
                    {updateSuggestions.map((suggestion, idx) => (
                      <div key={idx} className="bg-white border border-amber-100 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            suggestion.action === 'update' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {suggestion.action === 'update' ? '更新' : '新增'}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {suggestion.data.standard_number}
                          </span>
                        </div>
                        {suggestion.changes && suggestion.changes.length > 0 && (
                          <div className="ml-2 mt-2">
                            {suggestion.changes.map((change, cIdx) => (
                              <div key={cIdx} className="text-sm text-amber-700">
                                {change}
                              </div>
                            ))}
                          </div>
                        )}
                        {suggestion.action === 'create' && (
                          <div className="ml-2 mt-2 text-sm text-amber-700">
                            名称: {suggestion.data.standard_name}
                            <br />
                            状态: {suggestion.data.status}
                            <br />
                            来源: {suggestion.data.source}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-end">
                    <button
                      onClick={handleConfirmUpdates}
                      className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 text-sm font-medium transition-colors"
                    >
                      确认更新数据库
                    </button>
                  </div>
                </div>
              )}

              {aiResults.length > 0 && (
                <div className="mt-6">
                  <div className="px-4 py-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <h2 className="text-lg font-semibold text-gray-900">AI校验结果</h2>
                  </div>
                  <div className="overflow-x-auto mt-2">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">序号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">标准号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">输入名称</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">正确名称</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">说明</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {aiResults.map((r: any, idx: number) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-3 py-3 text-sm text-gray-900">{idx + 1}</td>
                            <td className="px-3 py-3 text-sm text-gray-900 font-mono">{r.number}</td>
                            <td className="px-3 py-3 text-sm text-gray-900">{r.name}</td>
                            <td className="px-3 py-3">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                r.status === '正确' ? 'bg-green-100 text-green-800' :
                                r.status === '已废止' ? 'bg-gray-100 text-gray-800' :
                                'bg-red-100 text-red-800'
                              }`}>{r.status}</span>
                            </td>
                            <td className="px-3 py-3 text-sm text-gray-900">{r.correct_name || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-500">{r.message || ''}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="mt-6 bg-blue-50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">使用说明</h3>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>步骤1：点击"解析文本"，系统自动从非结构化文本中提取规范信息</li>
                  <li>步骤2：确认提取结果后，点击"开始校验"进行规范校验</li>
                  <li>结果包含：正确、规范已过期、规范名称错误、规范标准号错误等状态</li>
                  <li>在线查询功能可联网获取最新规范状态（耗时较长）</li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'database' && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <input
                      type="text"
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                      placeholder="搜索标准号或名称..."
                      className="w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                    <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <button
                    onClick={handleSearch}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                  >
                    搜索
                  </button>
                  {searchKeyword && (
                    <button
                      onClick={handleClearSearch}
                      className="text-sm text-gray-600 hover:text-gray-800"
                    >
                      清空
                    </button>
                  )}
                </div>
                <button
                  onClick={handleAddStandard}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors"
                >
                  添加标准
                </button>
              </div>

              {dbLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">标准号</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">名称</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">发布日期</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">实施日期</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">替代标准</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
                          <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {standards.map((standard) => (
                          <tr key={standard.id} className="hover:bg-gray-50">
                            <td className="px-3 py-3 text-sm text-gray-900">{standard.id}</td>
                            <td className="px-3 py-3 text-sm text-gray-900 font-medium">{standard.standard_number}</td>
                            <td className="px-3 py-3 text-sm text-gray-600 max-w-xs truncate">{standard.standard_name}</td>
                            <td className="px-3 py-3">
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(standard.status)}`}>
                                {standard.status}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-sm text-gray-600">{standard.release_date || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-600">{standard.implement_date || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-600">{standard.replace_by || '-'}</td>
                            <td className="px-3 py-3 text-sm text-gray-600">{standard.source || '-'}</td>
                            <td className="px-3 py-3">
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleEditStandard(standard)}
                                  className="text-blue-600 hover:text-blue-800 text-sm"
                                >
                                  编辑
                                </button>
                                <button
                                  onClick={() => handleDeleteStandard(standard.id)}
                                  className="text-red-600 hover:text-red-800 text-sm"
                                >
                                  删除
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {standards.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        暂无数据
                      </div>
                    )}
                  </div>

                  {totalCount > pageSize && (
                    <div className="flex justify-between items-center mt-4 px-2">
                      <div className="text-sm text-gray-500">
                        共 {totalCount} 条记录，第 {currentPage}/{totalPages} 页
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => fetchStandards(1)}
                          disabled={currentPage === 1}
                          className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          首页
                        </button>
                        <button
                          onClick={() => fetchStandards(currentPage - 1)}
                          disabled={currentPage === 1}
                          className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          上一页
                        </button>
                        <button
                          onClick={() => fetchStandards(currentPage + 1)}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          下一页
                        </button>
                        <button
                          onClick={() => fetchStandards(totalPages)}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          末页
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {editingStandard ? '编辑标准' : '添加标准'}
              </h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标准号 *</label>
                  <input
                    type="text"
                    value={formData.standard_number}
                    onChange={(e) => setFormData({ ...formData, standard_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">标准名称 *</label>
                  <input
                    type="text"
                    value={formData.standard_name}
                    onChange={(e) => setFormData({ ...formData, standard_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="现行">现行</option>
                    <option value="废止">废止</option>
                    <option value="即将实施">即将实施</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">发布日期</label>
                    <input
                      type="date"
                      value={formData.release_date}
                      onChange={(e) => setFormData({ ...formData, release_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">实施日期</label>
                    <input
                      type="date"
                      value={formData.implement_date}
                      onChange={(e) => setFormData({ ...formData, implement_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">废止日期</label>
                    <input
                      type="date"
                      value={formData.abolish_date}
                      onChange={(e) => setFormData({ ...formData, abolish_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">替代标准号</label>
                    <input
                      type="text"
                      value={formData.replace_by}
                      onChange={(e) => setFormData({ ...formData, replace_by: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">来源</label>
                  <input
                    type="text"
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-between items-center mt-6">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm"
                >
                  取消
                </button>
                <button
                  onClick={handleSaveStandard}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">AI大模型配置</h3>
            <p className="text-sm text-gray-500 mb-4">
              配置AI大模型后，可使用"AI校验"功能，让AI判断规范名称和标准号是否正确匹配。
            </p>
            <div className="space-y-4 max-w-xl">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                <input
                  type="text"
                  value={aiBaseUrl}
                  onChange={(e) => setAiBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">OpenAI兼容接口地址，如 https://api.openai.com 或 https://api.deepseek.com</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Token</label>
                <input
                  type="password"
                  value={aiToken}
                  onChange={(e) => setAiToken(e.target.value)}
                  placeholder={aiHasToken ? '已配置（留空保持不变）' : 'sk-...'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                <input
                  type="text"
                  value={aiModel}
                  onChange={(e) => setAiModel(e.target.value)}
                  placeholder="gpt-3.5-turbo"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">如 gpt-4o、deepseek-chat、qwen-plus 等</p>
              </div>
              <button
                onClick={handleSaveAIConfig}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                保存配置
              </button>
              {aiHasToken && (
                <span className="text-sm text-green-600 ml-3">✓ 已配置</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App