/**
 * VLA可视化系统前端应用
 * 实现WebSocket连接、摄像头显示、图表绘制和控制面板功能
 */

class VLAVisualizationApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.fpsCounter = 0;
        this.lastFpsTime = Date.now();
        this.frameCount = 0;
        this.isPaused = false;
        
        // 图表更新优化相关属性
        this.charts = {};
        this.chartDataBuffer = {};
        this.chartUpdateTimer = null;
        this.chartUpdateInterval = 50; // 50ms更新一次图表，即20FPS
        this.pendingChartUpdate = false; // 标记是否有待更新的数据
        this.lastChartUpdateTime = 0;
        this.x_left_bound = 0;
        
        // 相机数据优化相关属性
        this.latestCameraData = {}; // 存储最新的相机数据
        this.cameraUpdateTimer = null;
        this.cameraUpdateInterval = 33; // 33ms更新一次相机，即30FPS
        this.pendingCameraUpdate = false; // 标记是否有待更新的相机数据
        this.lastCameraUpdateTime = 0;
        
        // WebSocket配置
        this.wsUrl = 'ws://localhost:8765';
        
        // 初始化应用
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.updateFPS();
        this.startChartUpdateTimer();
        this.startCameraUpdateTimer();
        this.connect();
        
        // 检查深色模式偏好
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }
    
    setupEventListeners() {
        // 侧边栏控制
        const menuToggle = document.getElementById('menuToggle');
        const closeSidebar = document.getElementById('closeSidebar');
        const overlay = document.getElementById('overlay');
        
        if (menuToggle) {
            menuToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSidebar();
            });
        }
        
        if (closeSidebar) {
            closeSidebar.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.closeSidebar();
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.closeSidebar();
            });
        }
        
        // Tab导航控制
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = e.target.closest('.tab-btn').dataset.tab;
                if (tabName) {
                    this.switchControlTab(tabName);
                }
            });
        });
        
        // 显示控制
        document.getElementById('showCameras').addEventListener('change', (e) => this.toggleCameraSection(e.target.checked));
        document.getElementById('showCharts').addEventListener('change', (e) => this.toggleChartsSection(e.target.checked));
        
        // 使用事件委托处理动态生成的元素
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('camera-toggle')) {
                this.toggleCamera(e.target.dataset.camera, e.target.checked);
            }
            if (e.target.classList.contains('joint-toggle')) {
                this.toggleJoint(e.target.dataset.joint, e.target.checked);
            }
            if (e.target.name === 'cameraControl') {
                this.handleCameraControlChange(e.target.value);
            }
            if (e.target.name === 'chartControl') {
                this.handleChartControlChange(e.target.value);
            }
        });
        
        // 使用事件委托处理关节图表tab按钮点击
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-button')) {
                const joint = e.target.dataset.joint;
                const tab = e.target.dataset.tab;
                if (joint && tab) {
                    this.switchTab(joint, tab);
                }
            }
        });
        
        // 主题控制
        document.getElementById('darkModeToggle').addEventListener('change', (e) => this.toggleDarkMode(e.target.checked));
        
        // 图表控制
        document.getElementById('pauseCharts').addEventListener('click', () => this.toggleChartsPause());
        document.getElementById('clearDataBtn').addEventListener('click', () => this.clearData());
        document.getElementById('exportDataBtn').addEventListener('click', () => this.exportData());
        
        // 全屏控制
        document.getElementById('fullscreenCameras').addEventListener('click', () => this.toggleFullscreen('camera-section'));
        document.getElementById('fullscreenCharts').addEventListener('click', () => this.toggleFullscreen('charts-section'));
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // 窗口大小变化
        window.addEventListener('resize', () => this.handleResize());
    }
    
    // WebSocket连接管理
    connect() {
        if (this.isConnected) return;
        
        try {
            this.websocket = new WebSocket(this.wsUrl);
            // 设置二进制数据类型为ArrayBuffer
            this.websocket.binaryType = 'arraybuffer';
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.showNotification('WebSocket连接成功', 'success');
                
                // 请求配置信息
                this.sendMessage({ type: 'get_config' });
            };
            
            this.websocket.onmessage = (event) => {
                // 检查是否为二进制数据
                if (event.data instanceof ArrayBuffer) {
                    this.handleBinaryMessage(event.data);
                } else {
                    // 文本消息（JSON）
                    this.handleMessage(JSON.parse(event.data));
                }
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.showNotification('WebSocket连接已断开', 'warning');
                
                // 自动重连
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.showNotification('尝试重新连接...', 'info');
                        this.connect();
                    }
                }, 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                this.showNotification('WebSocket连接错误', 'error');
            };
            
        } catch (error) {
            console.error('连接失败:', error);
            this.showNotification('无法连接到服务器', 'error');
        }
    }
    
    // 新增方法：处理二进制消息
    handleBinaryMessage(arrayBuffer) {
        try {
            const dataView = new DataView(arrayBuffer);
            
            // 读取头长度（前4字节）
            const headerLength = dataView.getUint32(0, false); // big-endian
            
            // 读取头数据
            const headerBytes = new Uint8Array(arrayBuffer, 4, headerLength);
            const headerText = new TextDecoder().decode(headerBytes);
            const header = JSON.parse(headerText);
            
            // 读取图像数据
            const imageData = new Uint8Array(arrayBuffer, 4 + headerLength);
            
            // 处理摄像头数据
            if (header.type === 'camera_data_binary') {
                this.handleBinaryCameraData(header, imageData);
            }
            
            this.updateFPSCounter();
        } catch (error) {
            console.error('处理二进制消息失败:', error);
        }
    }
    
    // 修改方法：处理二进制摄像头数据 - 只存储最新数据
    handleBinaryCameraData(header, imageData) {
        if (this.isPaused) return;
        
        const cameraId = header.camera_id;
        
        // 只存储最新的相机数据，不立即更新显示
        this.latestCameraData[cameraId] = {
            header: header,
            imageData: imageData,
            timestamp: Date.now()
        };
        
        // 标记有待更新的相机数据
        this.pendingCameraUpdate = true;
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        // 停止定时器
        this.stopChartUpdateTimer();
        this.stopCameraUpdateTimer();
    }
    
    sendMessage(message) {
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'config':
                this.handleConfig(data.data);
                break;
            case 'joint_data':
                this.handleJointData(data.data);
                break;
            case 'pong':
                // 心跳响应
                break;
            default:
                console.log('未知消息类型:', data.type);
        }
        
        this.updateFPSCounter();
    }
    
    handleConfig(config) {
        console.log('收到配置:', config);
        // 这里可以根据配置动态调整界面
    }
    
    handleJointData(jointData) {
        if (this.isPaused) return;
        
        // 新的数据格式：每次接收一个数据包，包含tab、type、x、joints_y
        const { tab, type, x, joints_y } = jointData;
        
        // 初始化数据缓存结构
        if (!this.chartDataBuffer[tab]) {
            this.chartDataBuffer[tab] = {};
        }
        if (!this.chartDataBuffer[tab][type]) {
            this.chartDataBuffer[tab][type] = [];
        }
        
        // 添加新数据点
        const dataPoint = {
            x: x,
            joints_y: joints_y,
            timestamp: Date.now()
        };
        
        this.chartDataBuffer[tab][type].push(dataPoint);

        if (type !== 'origin') {
            this.x_left_bound = x;
            this.chartDataBuffer[tab][type] = this.chartDataBuffer[tab][type].slice(-1500);
        }
        if (type === 'origin') {
            // && this.x_left_bound - this.chartDataBuffer[tab][type][0].x > 1500
            // // 遍历所有origin数据点，找到第一个x大于等于x_left_bound的点
            // let firstIndex = -1;
            // for (let i = 0; i < this.chartDataBuffer[tab][type].length; i++) {
            //     if (this.chartDataBuffer[tab][type][i].x >= this.x_left_bound) {
            //         firstIndex = i;
            //         break;
            //     }
            // }
            // console.log('firstIndex:', firstIndex, 'len:', this.chartDataBuffer[tab][type].length);
            // this.chartDataBuffer[tab][type] = this.chartDataBuffer[tab][type].slice(firstIndex);
            this.chartDataBuffer[tab][type] = this.chartDataBuffer[tab][type].slice(-parseInt(1500 / (420 / 64)));
        }
        
        // 标记有待更新的数据，但不立即更新图表
        this.pendingChartUpdate = true;
    }
    
    // 图表管理
    initializeCharts() {
        const container = document.getElementById('joint-charts-container');
        const joints = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6', 'joint_7', 'joint_8', 'joint_9', 'joint_10', 'joint_11', 'joint_12', 'joint_13', 'joint_14', 'joint_15', 'joint_16'];  // 16个关节
        const tabs = ['position', 'velocity', 'acceleration'];
        const tabLabels = { position: '位置', velocity: '速度', acceleration: '加速度' };
        const units = { position: 'rad', velocity: 'rad/s', acceleration: 'rad/s²' };
        
        joints.forEach((joint, jointIndex) => {
            // TODO: 只显示joint_1和joint_8
            if (jointIndex !==0 && jointIndex !== 7) return;

            const jointDiv = document.createElement('div');
            jointDiv.className = 'joint-chart';
            jointDiv.dataset.joint = joint;
            
            jointDiv.innerHTML = `
                <div class="joint-header">
                    <span class="joint-title">${joint}</span>
                    <div class="joint-tabs">
                        ${tabs.map(tab => `
                            <button class="tab-button ${tab === 'position' ? 'active' : ''}" 
                                    data-joint="${joint}" data-tab="${tab}">
                                ${tabLabels[tab]}
                            </button>
                        `).join('')}
                    </div>
                </div>
                <div class="chart-container">
                    <canvas class="chart-canvas" id="chart-${joint}"></canvas>
                </div>
            `;
            
            container.appendChild(jointDiv);
            
            // 初始化图表
            const canvas = document.getElementById(`chart-${joint}`);
            const ctx = canvas.getContext('2d');
            
            this.charts[joint] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: `${joint} - position`,
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false,
                    scales: {
                        x: {
                            type: 'linear',
                            title: {
                                display: true,
                                text: 'step'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: `position (${units.position})`
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#2563eb',
                            borderWidth: 1
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
        });
    }
    
    switchTab(joint, tab) {
        const jointDiv = document.querySelector(`[data-joint="${joint}"]`);
        const buttons = jointDiv.querySelectorAll('.tab-button');
        
        // 更新按钮状态
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // 更新图表数据
        this.updateChartForJoint(joint);
    }
    
    updateChartForJoint(joint) {
        const chart = this.charts[joint];
        if (!chart) return;
        
        const jointDiv = document.querySelector(`[data-joint="${joint}"]`);
        const activeTabButton = jointDiv.querySelector('.tab-button.active');
        
        if (!activeTabButton) return;
        
        const tab = activeTabButton.dataset.tab;
        
        const tabLabels = { position: 'position', velocity: 'velocity', acceleration: 'acceleration' };
        const units = { position: 'rad', velocity: 'rad/s', acceleration: 'rad/s²' };
        
        // 获取所有三种类型的数据
        const originData = this.getChartData(tab, 'origin', joint);
        const actionData = this.getChartData(tab, 'action', joint);
        const stateData = this.getChartData(tab, 'state', joint);
        
        // 更新图表数据集
        chart.data.datasets = [
            {
                label: 'Origin',
                data: originData.labels.map((x, i) => ({ x, y: originData.data[i] })),
                pointRadius: 0,
                // borderColor: 'rgb(75, 192, 192)',
                // backgroundColor: 'rgba(75, 192, 192, 0.1)',
                // tension: 0.4,
                // pointStyle: 'circle',
                // borderWidth: 2,
                // fill: false,
                // pointHoverRadius: 5
            },
            {
                label: 'Action',
                data: actionData.labels.map((x, i) => ({ x, y: actionData.data[i] })),
                pointRadius: 0,
                // borderColor: 'rgb(255, 99, 132)',
                // backgroundColor: 'rgba(255, 99, 132, 0.1)',
            },
            {
                label: 'State',
                data: stateData.labels.map((x, i) => ({ x, y: stateData.data[i] })),
                pointRadius: 0,
                // borderColor: 'rgb(54, 162, 235)',
                // backgroundColor: 'rgba(54, 162, 235, 0.1)',
            }
        ];
        
        // 更新Y轴标题
        chart.options.scales.y.title.text = `${tabLabels[tab]} (${units[tab]})`;
        
        chart.update('none');
    }
    
    getChartData(tab, type, joint) {
        if (!this.chartDataBuffer[tab] || !this.chartDataBuffer[tab][type]) {
            return { labels: [], data: [] };
        }
        
        const jointIndex = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6', 'joint_7', 'joint_8', 'joint_9', 'joint_10', 'joint_11', 'joint_12', 'joint_13', 'joint_14', 'joint_15', 'joint_16'].indexOf(joint);
        if (jointIndex === -1) return { labels: [], data: [] };
        
        const buffer = this.chartDataBuffer[tab][type];
        return {
            labels: buffer.map(point => point.x),
            data: buffer.map(point => point.joints_y[jointIndex])
        };
    }
    
    updateChartsWithNewData() {
        // 更新所有可见的图表
        Object.keys(this.charts).forEach(joint => {
            this.updateChartForJoint(joint);
        });
    }
    
    // 新增：启动图表更新定时器
    startChartUpdateTimer() {
        if (this.chartUpdateTimer) {
            clearInterval(this.chartUpdateTimer);
        }
        
        this.chartUpdateTimer = setInterval(() => {
            this.updateChartsIfNeeded();
        }, this.chartUpdateInterval);
    }
    
    // 新增：停止图表更新定时器
    stopChartUpdateTimer() {
        if (this.chartUpdateTimer) {
            clearInterval(this.chartUpdateTimer);
            this.chartUpdateTimer = null;
        }
    }
    
    // 新增：按需更新图表
    updateChartsIfNeeded() {
        if (!this.pendingChartUpdate || this.isPaused) {
            return;
        }
        
        const now = Date.now();
        // 防止更新过于频繁
        if (now - this.lastChartUpdateTime < this.chartUpdateInterval) {
            return;
        }
        
        this.updateChartsWithNewData();
        this.pendingChartUpdate = false;
        this.lastChartUpdateTime = now;
    }
    
    // 新增：设置图表更新频率
    setChartUpdateInterval(interval) {
        this.chartUpdateInterval = Math.max(10, interval); // 最小10ms
        this.stopChartUpdateTimer();
        this.startChartUpdateTimer();
    }
    
    // 相机更新定时器相关方法
    startCameraUpdateTimer() {
        if (this.cameraUpdateTimer) {
            clearInterval(this.cameraUpdateTimer);
        }
        
        this.cameraUpdateTimer = setInterval(() => {
            this.updateCameraIfNeeded();
        }, this.cameraUpdateInterval);
    }
    
    stopCameraUpdateTimer() {
        if (this.cameraUpdateTimer) {
            clearInterval(this.cameraUpdateTimer);
            this.cameraUpdateTimer = null;
        }
    }
    
    updateCameraIfNeeded() {
        if (!this.pendingCameraUpdate || this.isPaused) {
            return;
        }
        
        const now = Date.now();
        
        // 防抖处理
        if (now - this.lastCameraUpdateTime < this.cameraUpdateInterval) {
            return;
        }
        
        // 更新所有有新数据的相机
        Object.keys(this.latestCameraData).forEach(cameraId => {
            this.updateCameraDisplay(cameraId, this.latestCameraData[cameraId]);
        });
        
        this.pendingCameraUpdate = false;
        this.lastCameraUpdateTime = now;
    }
    
    updateCameraDisplay(cameraId, cameraData) {
        const imageElement = document.getElementById(`camera_${cameraId}`);
        const container = document.querySelector(`[data-camera="${cameraId}"]`);
        
        if (imageElement && container && !container.classList.contains('hidden')) {
            // 创建Blob对象
            const blob = new Blob([cameraData.imageData], { type: 'image/jpeg' });
            const imageUrl = URL.createObjectURL(blob);
            
            // 预加载图像以减少卡顿
            const img = new Image();
            img.onload = () => {
                // 释放之前的URL
                if (imageElement.src && imageElement.src.startsWith('blob:')) {
                    URL.revokeObjectURL(imageElement.src);
                }
                
                imageElement.src = imageUrl;
                imageElement.classList.add('loaded');
            };
            img.onerror = () => {
                URL.revokeObjectURL(imageUrl);
                console.error(`摄像头${cameraId}图像加载失败`);
            };
            img.src = imageUrl;
        }
    }
    
    setCameraUpdateInterval(interval) {
        this.cameraUpdateInterval = Math.max(16, interval); // 最小16ms (约60FPS)
        this.stopCameraUpdateTimer();
        this.startCameraUpdateTimer();
    }
    
    // UI控制方法
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const mainContent = document.getElementById('main-content');
        
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
            
            if (window.innerWidth > 768 && mainContent) {
                mainContent.classList.toggle('sidebar-open');
            }
        }
    }
    
    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const mainContent = document.getElementById('main-content');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
            if (mainContent) {
                mainContent.classList.remove('sidebar-open');
            }
        }
    }
    
    updateConnectionStatus(connected) {
        const statusText = connected ? '已连接' : '未连接';
        const dotClass = connected ? 'connected' : 'disconnected';
        document.getElementById('headerConnectionStatus').textContent = statusText;
        document.getElementById('headerStatusDot').className = `status-dot ${dotClass}`;
    }
    
    toggleCameraSection(show) {
        const section = document.getElementById('camera-section');
        section.style.display = show ? 'block' : 'none';
    }
    
    toggleChartsSection(show) {
        const section = document.getElementById('charts-section');
        section.style.display = show ? 'block' : 'none';
    }
    
    toggleCamera(cameraIndex, show) {
        const container = document.querySelector(`[data-camera="${cameraIndex}"]`);
        if (container) {
            container.classList.toggle('hidden', !show);
        }
    }
    
    toggleJoint(joint, show) {
        const container = document.querySelector(`[data-joint="${joint}"]`);
        if (container) {
            container.classList.toggle('hidden', !show);
        }
    }
    
    toggleDarkMode(enabled) {
        if (enabled) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        
        // 更新图表主题
        Object.values(this.charts).forEach(chart => {
            const isDark = enabled;
            chart.options.scales.x.grid.color = isDark ? '#334155' : '#e2e8f0';
            chart.options.scales.y.grid.color = isDark ? '#334155' : '#e2e8f0';
            chart.options.scales.x.ticks.color = isDark ? '#cbd5e1' : '#64748b';
            chart.options.scales.y.ticks.color = isDark ? '#cbd5e1' : '#64748b';
            chart.options.plugins.legend.labels.color = isDark ? '#f8fafc' : '#1e293b';
            chart.update('none');
        });
    }
    
    toggleChartsPause() {
        this.isPaused = !this.isPaused;
        const pauseBtn = document.getElementById('pauseCharts');
    
        if (this.isPaused) {
            pauseBtn.textContent = '恢复图表';
            pauseBtn.classList.add('paused');
            this.showNotification('图表已暂停', 'info');
            // 暂停时停止定时器
            this.stopChartUpdateTimer();
            this.stopCameraUpdateTimer();
        } else {
            pauseBtn.textContent = '暂停图表';
            pauseBtn.classList.remove('paused');
            this.showNotification('图表已恢复', 'success');
            // 恢复时重启定时器
            this.startChartUpdateTimer();
            this.startCameraUpdateTimer();
        }
    }
    
    clearData() {
        if (confirm('确定要清除所有数据吗？')) {
            // 清空图表数据缓存
            this.chartDataBuffer = {};
            
            // 清空所有图表
            Object.values(this.charts).forEach(chart => {
                chart.data.labels = [];
                chart.data.datasets[0].data = [];
                chart.update('none');
            });
            this.showNotification('数据已清除', 'success');
        }
    }
    
    exportData() {
        const data = {
            timestamp: new Date().toISOString(),
            chartDataBuffer: this.chartDataBuffer,
            latestCameraData: Object.keys(this.latestCameraData)
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vla_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showNotification('数据已导出', 'success');
    }
    
    toggleFullscreen(elementId) {
        const element = document.getElementById(elementId);
        if (!document.fullscreenElement) {
            element.requestFullscreen().catch(err => {
                console.error('无法进入全屏模式:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    // 工具方法
    updateFPSCounter() {
        this.frameCount++;
        const now = Date.now();
        
        if (now - this.lastFpsTime >= 1000) {
            this.fpsCounter = Math.round((this.frameCount * 1000) / (now - this.lastFpsTime));
            document.getElementById('fpsCounter').textContent = this.fpsCounter;
            
            this.frameCount = 0;
            this.lastFpsTime = now;
        }
    }
    
    updateFPS() {
        // 定期更新FPS显示
        setInterval(() => {
            if (this.frameCount === 0) {
                document.getElementById('fpsCounter').textContent = '0';
            }
        }, 2000);
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <i class="${icons[type]}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(notification);
        
        // 自动移除通知
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    handleKeyboard(event) {
        // 键盘快捷键
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'm':
                    event.preventDefault();
                    this.toggleSidebar();
                    break;
                case 'k':
                    event.preventDefault();
                    if (this.isConnected) {
                        this.disconnect();
                    } else {
                        this.connect();
                    }
                    break;
                case 'p':
                    event.preventDefault();
                    this.toggleChartsPause();
                    break;
            }
        }
        
        if (event.key === 'Escape') {
            this.closeSidebar();
        }
    }
    
    handleResize() {
        // 响应式处理
        if (window.innerWidth <= 768) {
            const mainContent = document.getElementById('main-content');
            mainContent.classList.remove('sidebar-open');
        }
        
        // 重新调整图表大小
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }
    
    // 控制面板Tab切换
    switchControlTab(tabName) {
        // 更新tab按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // 显示对应的tab内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }
    
    // 摄像头控制radio button处理
    handleCameraControlChange(value) {
        const cameras = document.querySelectorAll('.camera-container');
        cameras.forEach((camera, index) => {
            const cameraElement = camera.querySelector('.camera-image');
            if (value === 'all') {
                camera.style.display = 'block';
            } else if (value === 'none') {
                camera.style.display = 'none';
            } else if (value === `camera_${index}`) {
                camera.style.display = 'block';
            } else {
                camera.style.display = 'none';
            }
        });
    }
    
    // 图表控制radio button处理
    handleChartControlChange(value) {
        const charts = document.querySelectorAll('.joint-chart');
        charts.forEach((chart, index) => {
            if (value === 'all') {
                chart.style.display = 'block';
            } else if (value === 'none') {
                chart.style.display = 'none';
            } else if (value === `joint_${index + 1}`) {
                chart.style.display = 'block';
            } else {
                chart.style.display = 'none';
            }
        });
        
        // 触发图表重绘
        setTimeout(() => {
            Object.values(this.charts).forEach(chart => {
                if (chart && chart.canvas.offsetParent !== null) {
                    chart.resize();
                }
            });
        }, 100);
     }
     
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.vlaApp = new VLAVisualizationApp();
});
