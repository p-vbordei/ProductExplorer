import { Component, OnInit, OnDestroy } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Product } from '../../api/product';
import { ProductService } from '../../service/product.service';
import { Subscription } from 'rxjs';
import { LayoutService } from 'src/app/layout/service/app.layout.service';
import * as FileSaver from 'file-saver';

interface Column {
    field: string;
    header: string;
    customExportHeader?: string;
}

interface ExportColumn {
    title: string;
    dataKey: string;
}

@Component({
  selector: 'app-customer-insights',
  templateUrl: './customer-insights.component.html',
  styleUrls: ['./customer-insights.component.scss']
})
export class CustomerInsightsComponent implements OnInit, OnDestroy  {

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

  exportColumns!: ExportColumn[];

  positiveFeedbackData!: any;

  subscription!: Subscription;

  constructor(private productService: ProductService, public layoutService: LayoutService) {
      this.subscription = this.layoutService.configUpdate$.subscribe(() => {
          this.initCharts();
      });
  }

  ngOnInit() {
      this.initCharts();
      this.initTables();
      this.productService.getProductsSmall().then(data => this.products = data);

      this.items = [
          { label: 'Add New', icon: 'pi pi-fw pi-plus' },
          { label: 'Remove', icon: 'pi pi-fw pi-minus' }
      ];

      this.cols = [
        { field: 'label', header: 'Feedback Topic' },
        { field: 'value', header: 'Percentage' },
        { field: 'description', header: 'Reasons for Feedback' }
        // { field: 'count', header: 'Reasons for Positive Feedback' }
    ];

    this.exportColumns = this.cols.map((col) => ({ title: col.header, dataKey: col.field }));
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
                  label: 'First Dataset',
                  data: [100, 80, 30],
                  fill: false,
                  backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                  borderColor: documentStyle.getPropertyValue('--indigo-400'),
                  tension: .4
              },
              {
                  label: 'Second Dataset',
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
                label: 'First Dataset',
                data: [210, 100, 300],
                fill: false,
                backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                borderColor: documentStyle.getPropertyValue('--indigo-400'),
                tension: .4
            },
            {
                label: 'Second Dataset',
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
                label: 'First Dataset',
                data: [123, 170, 30],
                fill: false,
                backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                borderColor: documentStyle.getPropertyValue('--indigo-400'),
                tension: .4
            },
            {
                label: 'Second Dataset',
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
                label: 'First Dataset',
                data: [321, 555, 90],
                fill: false,
                backgroundColor: documentStyle.getPropertyValue('--indigo-400'),
                borderColor: documentStyle.getPropertyValue('--indigo-400'),
                tension: .4
            },
            {
                label: 'Second Dataset',
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
    this.positiveFeedbackData = [
        {
          "label": "Good Sound Quality",
          "value": 56.3,
          "description": "Customers have reported good bass and sound quality, as well as decent sound for phone calls. This can be a selling point for users who are looking for a high-quality and immersive listening experience.",
          "count": 22032
        },
        {
          "label": "Comfortable Fit",
          "value": 23.7,
          "description": "Customers have reported that the earbuds are comfortable to wear and have a well-fitting design, which can be a selling point for users who are looking for a comfortable and secure fit.",
          "count": 9269
        },
        {
          "label": "Excellent Value",
          "value": 20.0,
          "description": "Customers have reported that the earbuds offer good quality and sound for the price, and some have even described them as a great value for the price. This can be a selling point for users who are looking for a high-quality pair of earbuds at an affordable price.",
          "count": 7839
        },
        {
          "label": "Long Battery Life",
          "value": 16.8,
          "description": "Customers have found these earbuds to have good battery life and are good for recharging with the case, although some have noted that the battery life could be improved.",
          "count": 6591
        },
        {
          "label": "Noise Cancellation",
          "value": 12.1,
          "description": "Customers have found these earbuds to have good noise isolation and noise cancellation for the price, which is helpful for drowning out noise.",
          "count": 4745
        },
        {
          "label": "Easy Connectivity",
          "value": 11.0,
          "description": "Customers have reported that the earbuds have good wireless connectivity and are easy to pair with their phone or other devices, which can be a selling point for users who are looking for a hassle-free listening experience.",
          "count": 4289
        },
        {
          "label": "Stays In Ear",
          "value": 10.5,
          "description": "Customers have found these earbuds to fit well, with multiple sized earbud tips and a good fit overall.",
          "count": 4092
        },
        {
          "label": "Easy To Use",
          "value": 9.7,
          "description": "Customers have reported that the earbuds are very easy to set up and use, with some describing them as useful and feature-rich. This can be a selling point for users who are looking for a user-friendly and convenient pair of earbuds.",
          "count": 3777
        },
        {
          "label": "Compact Design",
          "value": 6.6,
          "description": "Customers have reported that the case has a compact and sleek design, which can be a selling point for users who are looking for a stylish and portable pair of earbuds.",
          "count": 2578
        },
        {
          "label": "Clear Voice Calls",
          "value": 6.4,
          "description": "Customers have reported decent to excellent sound quality for voice calls, which can be a selling point for users who frequently use their earbuds for phone calls.",
          "count": 2492
        }
      ]      
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

