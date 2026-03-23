odoo.define("quan_ly_van_ban.dashboard", function (require) {
    "use strict";

    const AbstractAction = require("web.AbstractAction");
    const ajax = require("web.ajax");
    const core = require("web.core");

    const QWeb = core.qweb;
    const actionRegistry = core.action_registry;

    const VanBanDashboard = AbstractAction.extend({
        className: "o_van_ban_dashboard_action",
        events: {
            "click .o_van_ban_dashboard_action_link": "_onOpenAction",
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
                    model: "van_ban_den",
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
            while (this._charts.length) {
                const chart = this._charts.pop();
                if (chart) {
                    chart.destroy();
                }
            }
            this._super.apply(this, arguments);
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
                    datasets: [{
                        label: datasetLabel,
                        data: values,
                        backgroundColor: color,
                        borderColor: color,
                        borderWidth: 1,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {display: true, position: "top"},
                    scales: {
                        yAxes: [{
                            ticks: {beginAtZero: true, precision: 0},
                        }],
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
                    datasets: [{
                        label: datasetLabel,
                        data: values,
                        borderColor: color,
                        backgroundColor: "rgba(14, 165, 233, 0.12)",
                        fill: true,
                        lineTension: 0.2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {display: true, position: "top"},
                    scales: {
                        yAxes: [{
                            ticks: {beginAtZero: true, precision: 0},
                        }],
                    },
                },
            });
            this._charts.push(chart);
        },

        _makeDoughnutChart(canvasSelector, labels, values, colors) {
            const canvas = this.el.querySelector(canvasSelector);
            if (!canvas) {
                return;
            }
            const chart = new Chart(canvas, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {display: true, position: "top"},
                },
            });
            this._charts.push(chart);
        },

        _renderCharts() {
            const incomingData = this.dashboardData.charts.monthly_incoming || [];
            this._makeBarChart(
                ".o_van_ban_monthly_incoming_chart",
                incomingData.map((item) => item.label),
                incomingData.map((item) => item.value),
                "Văn bản đến",
                "rgba(34, 197, 94, 0.75)"
            );

            const outgoingData = this.dashboardData.charts.monthly_outgoing || [];
            this._makeLineChart(
                ".o_van_ban_monthly_outgoing_chart",
                outgoingData.map((item) => item.label),
                outgoingData.map((item) => item.value),
                "Văn bản đi",
                "rgba(37, 99, 235, 1)"
            );

            const employeeData = this.dashboardData.charts.employee_workload || [];
            this._makeBarChart(
                ".o_van_ban_employee_chart",
                employeeData.map((item) => item.label),
                employeeData.map((item) => item.value),
                "Số lượng văn bản",
                "rgba(249, 115, 22, 0.78)"
            );

            const statusData = this.dashboardData.charts.status_distribution || [];
            this._makeDoughnutChart(
                ".o_van_ban_status_chart",
                statusData.map((item) => item.label),
                statusData.map((item) => item.value),
                ["#94a3b8", "#f59e0b", "#16a34a"]
            );

            const priorityData = this.dashboardData.charts.priority_distribution || [];
            this._makeDoughnutChart(
                ".o_van_ban_priority_chart",
                priorityData.map((item) => item.label),
                priorityData.map((item) => item.value),
                ["#cbd5e1", "#38bdf8", "#f97316", "#dc2626"]
            );
        },

        _renderDashboard() {
            this.$el.html(
                QWeb.render("quan_ly_van_ban.DashboardMain", {
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

    actionRegistry.add("quan_ly_van_ban_dashboard", VanBanDashboard);

    return VanBanDashboard;
});
