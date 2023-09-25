import { Component, OnInit, OnDestroy } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Product } from '../../../api/product';
import { CustomerInsightsService } from '../../../service/customer-insights.service';
import { Subscription } from 'rxjs';
import { LayoutService } from 'src/app/layout/service/app.layout.service';
import * as FileSaver from 'file-saver';
import { ActivatedRoute } from '@angular/router';

interface Column {
    field: string;
    header: string;
    customExportHeader?: string;
}

@Component({
    selector: 'app-customer-insights',
    templateUrl: './customer-insights.component.html',
    styleUrls: ['./customer-insights.component.scss']
})
export class CustomerInsightsComponent implements OnInit, OnDestroy {

    items!: MenuItem[];

    products!: Product[];

    whoChartData: any;

    whoChartOptions: any;

    whatChartData: any;

    whatChartOptions: any;

    whereChartData: any;

    whereChartOptions: any;

    whenChartData: any;

    whenChartOptions: any;

    cols!: Column[];

    buyersMotivationCols!: Column[];

    customerExpectationsCols!: Column[];

    positiveFeedbackData!: any;

    negativeFeedbackData!: any;

    buyersMotivationData!: any;

    customerExpectationsData!: any;

    subscription!: Subscription;
    tables!: any;
    tablesKeys!: any;


    constructor(private route: ActivatedRoute, public layoutService: LayoutService, private customerInsightsService: CustomerInsightsService) {
    }

    ngOnInit() {
        const investigationId = this.route.snapshot.paramMap.get('id');
        this.layoutService.state.selectedInvestigationId = investigationId;
        this.layoutService.onStateUpdate();

        this.initCharts();
        this.initTables();


        this.items = [
            { label: 'Add New', icon: 'pi pi-fw pi-plus' },
            { label: 'Remove', icon: 'pi pi-fw pi-minus' }
        ];

        this.cols = [
            { field: 'label', header: 'Feedback Topic' },
            { field: 'percentage', header: 'Percentage' },
            { field: 'numberOfObservations', header: 'Number of observations' },
            { field: 'rating', header: 'Rating' },
            { field: 'customerVoice', header: 'Customer Voice' }
            // { field: 'count', header: 'Reasons for Positive Feedback' }
        ];
    }

    getDocumentData(id) {
        this.customerInsightsService.getCustomerInsights(id).subscribe(data => {
            return data;
        });
    }


    initCharts() {
        const documentStyle = getComputedStyle(document.documentElement);
        const textColor = documentStyle.getPropertyValue('--text-color');
        const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary');
        const surfaceBorder = documentStyle.getPropertyValue('--surface-border');

        this.whoChartData = {
            labels: ['Kids', 'Moms', 'Grandpas'],
            datasets: [
                {
                    label: '1~3 stars',
                    data: [100, 80, 30],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                    borderColor: documentStyle.getPropertyValue('--indigo-400'),
                    tension: .4
                },
                {
                    label: '4~5 stars',
                    data: [570, 400, 200],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--teal-400'),
                    borderColor: documentStyle.getPropertyValue('--teal-400'),
                    tension: .4
                }
            ]
        };

        this.whoChartOptions = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                }
            }
        };

        this.whatChartData = {
            labels: ['Groceries', 'Gifts', 'Giraffe Fights'],
            datasets: [
                {
                    label: '1~3 stars',
                    data: [210, 100, 300],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                    borderColor: documentStyle.getPropertyValue('--indigo-400'),
                    tension: .4
                },
                {
                    label: '4~5 stars',
                    data: [570, 400, 200],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--teal-400'),
                    borderColor: documentStyle.getPropertyValue('--teal-400'),
                    tension: .4
                }
            ]
        };

        this.whatChartOptions = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                }
            }
        };

        this.whereChartData = {
            labels: ['Home', 'Park', 'Interstellar Gap'],
            datasets: [
                {
                    label: '1~3 stars',
                    data: [123, 170, 30],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                    borderColor: documentStyle.getPropertyValue('--indigo-400'),
                    tension: .4
                },
                {
                    label: '4~5 stars',
                    data: [570, 400, 200],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--teal-400'),
                    borderColor: documentStyle.getPropertyValue('--teal-400'),
                    tension: .4
                }
            ]
        };

        this.whereChartOptions = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                }
            }
        };

        this.whenChartData = {
            labels: ['Morning', 'Afternoon', 'Night'],
            datasets: [
                {
                    label: '1~3 stars',
                    data: [321, 555, 90],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                    borderColor: documentStyle.getPropertyValue('--indigo-400'),
                    tension: .4
                },
                {
                    label: '4~5 stars',
                    data: [570, 400, 200],
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--teal-400'),
                    borderColor: documentStyle.getPropertyValue('--teal-400'),
                    tension: .4
                }
            ]
        };

        this.whenChartOptions = {
            indexAxis: 'y',
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                },
                y: {
                    stacked: true,
                    ticks: {
                        color: textColorSecondary
                    },
                    grid: {
                        color: surfaceBorder,
                        drawBorder: false
                    }
                }
            }
        };
    }

    initTables() {
        this.subscription = this.customerInsightsService.getCustomerInsights(this.layoutService.state.selectedInvestigationId).subscribe(data => {
            this.tables = data.subcollections;
            this.tablesKeys = Object.keys(data.subcollections).map(key => {
                let words = [];
                let currentWord = [key[0].toUpperCase()];  // Start with the first character capitalized
            
                for (let i = 1; i < key.length; i++) {
                    if (key[i] === key[i].toUpperCase()) {
                        words.push(currentWord.join(''));
                        currentWord = [key[i].toUpperCase()];
                    } else {
                        currentWord.push(key[i]);
                    }
                }
            
                words.push(currentWord.join(''));
                return {
                    originalKey: key,
                    title: words.join(' ')
                };
            });
        });
    }

    ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }

    exportExcel(data: any) {
        import('xlsx').then((xlsx) => {
            const worksheet = xlsx.utils.json_to_sheet(data);
            const workbook = { Sheets: { data: worksheet }, SheetNames: ['data'] };
            const excelBuffer: any = xlsx.write(workbook, { bookType: 'xlsx', type: 'array' });
            this.saveAsExcelFile(excelBuffer, 'products');
        });
    }

    saveAsExcelFile(buffer: any, fileName: string): void {
        let EXCEL_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
        let EXCEL_EXTENSION = '.xlsx';
        const data: Blob = new Blob([buffer], {
            type: EXCEL_TYPE
        });
        FileSaver.saveAs(data, fileName + '_export_' + new Date().getTime() + EXCEL_EXTENSION);
    }
}

