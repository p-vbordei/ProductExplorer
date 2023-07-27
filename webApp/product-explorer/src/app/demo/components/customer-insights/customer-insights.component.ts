import { Component, OnInit, OnDestroy } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Product } from '../../api/product';
import { ProductService } from '../../service/product.service';
import { Subscription } from 'rxjs';
import { LayoutService } from 'src/app/layout/service/app.layout.service';

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


  subscription!: Subscription;

  constructor(private productService: ProductService, public layoutService: LayoutService) {
      this.subscription = this.layoutService.configUpdate$.subscribe(() => {
          this.initCharts();
      });
  }

  ngOnInit() {
      this.initCharts();
      this.productService.getProductsSmall().then(data => this.products = data);

      this.items = [
          { label: 'Add New', icon: 'pi pi-fw pi-plus' },
          { label: 'Remove', icon: 'pi pi-fw pi-minus' }
      ];
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

  ngOnDestroy() {
      if (this.subscription) {
          this.subscription.unsubscribe();
      }
  }
}

