odoo.define("nhan_su.dashboard", function (require) {
    "use strict";

    const AbstractAction = require("web.AbstractAction");
    const ajax = require("web.ajax");
    const core = require("web.core");

    const QWeb = core.qweb;
    const actionRegistry = core.action_registry;

    const NhanSuDashboard = AbstractAction.extend({
        className: "o_nhan_su_dashboard_action",
        events: {
            "click .o_nhan_su_dashboard_action_link": "_onOpenAction",
        },

        init() {
            this._super.apply(this, arguments);
            this.dashboardData = {};
            this._charts = [];
        },

        willStart() {
            return Promise.all([
                this._super.apply(this, arguments),
                ajax.loadJS("/web/static/lib/Chart/Chart.js"),
                this._rpc({
                    model: "nhan_vien",
                    method: "get_dashboard_data",
                    args: [],
                }).then((data) => {
                    this.dashboardData = data;
                }),
            ]);
        },

        start() {
            this._renderDashboard();
            return this._super.apply(this, arguments);
        },

        destroy() {
            this._destroyCharts();
            this._super.apply(this, arguments);
        },

        _destroyCharts() {
            while (this._charts.length) {
                const chart = this._charts.pop();
                if (chart) {
                    chart.destroy();
                }
            }
        },

        _makeBarChart(canvasSelector, labels, values, datasetLabel, color) {
            const canvas = this.el.querySelector(canvasSelector);
            if (!canvas) {
                return;
            }
            const chart = new Chart(canvas, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: datasetLabel,
                            data: values,
                            backgroundColor: color,
                            borderColor: color,
                            borderWidth: 1,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: true,
                        position: "top",
                    },
                    scales: {
                        yAxes: [
                            {
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0,
                                },
                            },
                        ],
                    },
                },
            });
            this._charts.push(chart);
        },

        _makeLineChart(canvasSelector, labels, values, datasetLabel, color) {
            const canvas = this.el.querySelector(canvasSelector);
            if (!canvas) {
                return;
            }
            const chart = new Chart(canvas, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: datasetLabel,
                            data: values,
                            borderColor: color,
                            backgroundColor: "rgba(59, 130, 246, 0.12)",
                            fill: true,
                            lineTension: 0.2,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: true,
                        position: "top",
                    },
                    scales: {
                        yAxes: [
                            {
                                ticks: {
                                    beginAtZero: true,
                                    precision: 0,
                                },
                            },
                        ],
                    },
                },
            });
            this._charts.push(chart);
        },

        _makeDoughnutChart(canvasSelector, labels, values) {
            const canvas = this.el.querySelector(canvasSelector);
            if (!canvas) {
                return;
            }
            const chart = new Chart(canvas, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            data: values,
                            backgroundColor: ["#16a34a", "#dc2626"],
                            borderWidth: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: true,
                        position: "top",
                    },
                },
            });
            this._charts.push(chart);
        },

        _renderCharts() {
            this._destroyCharts();

            const departmentData = this.dashboardData.charts.department || [];
            this._makeBarChart(
                ".o_nhan_su_department_chart",
                departmentData.map((item) => item.label),
                departmentData.map((item) => item.value),
                "Số lượng nhân sự",
                "rgba(59, 130, 246, 0.75)"
            );

            const trendData = this.dashboardData.charts.hiring_trend || [];
            this._makeLineChart(
                ".o_nhan_su_trend_chart",
                trendData.map((item) => item.label),
                trendData.map((item) => item.value),
                "Biến động nhân sự",
                "rgba(37, 99, 235, 1)"
            );

            const ageData = this.dashboardData.charts.age_distribution || [];
            this._makeBarChart(
                ".o_nhan_su_age_chart",
                ageData.map((item) => item.label),
                ageData.map((item) => item.value),
                "Số lượng nhân sự",
                "rgba(239, 68, 68, 0.78)"
            );

            const rewardData = this.dashboardData.charts.reward_ratio || [];
            this._makeDoughnutChart(
                ".o_nhan_su_reward_chart",
                rewardData.map((item) => item.label),
                rewardData.map((item) => item.value)
            );
        },

        _renderDashboard() {
            this.$el.html(
                QWeb.render("nhan_su.DashboardMain", {
                    dashboard: this.dashboardData,
                })
            );
            this._renderCharts();
        },

        _onOpenAction(ev) {
            ev.preventDefault();
            const actionXmlid = ev.currentTarget.dataset.actionXmlid;
            if (actionXmlid) {
                this.do_action(actionXmlid);
            }
        },
    });

    actionRegistry.add("nhan_su_dashboard", NhanSuDashboard);

    return NhanSuDashboard;
});
