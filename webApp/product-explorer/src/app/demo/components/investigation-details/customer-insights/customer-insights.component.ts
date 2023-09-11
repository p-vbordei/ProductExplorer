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


    constructor(private route: ActivatedRoute, public layoutService: LayoutService,private customerInsightsService: CustomerInsightsService) {
    }

    ngOnInit() {
        const investigationId = this.route.snapshot.paramMap.get('id');
        this.layoutService.state.selectedInvestigationId = investigationId;
        this.layoutService.onStateUpdate();
        
        console.log(this.getDocumentData(investigationId))

        this.initCharts();
        this.initTables();
        

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

        this.buyersMotivationCols = [
            { field: 'label', header: 'Buyers Motivation' },
            { field: 'value', header: 'Percentage' },
            { field: 'description', header: 'Reasons for buyers motivation' }
            // { field: 'count', header: 'Reasons for Positive Feedback' }
        ];

        this.customerExpectationsCols = [
            { field: 'label', header: 'Customer Unmet Needs' },
            { field: 'value', header: 'Percentage' },
            { field: 'description', header: 'Reason for Customer Unmet Needs' }
            // { field: 'count', header: 'Reasons for Positive Feedback' }
        ];


    }

    getDocumentData(id) { 
        return [
            {
                "clusters": [
                    {
                        "clusterLabel": "Good value for the price, Great value for the price",
                        "observationCount": 12,
                        "totalNumberOfObservations": 18,
                        "percentageOfObservationsVsTotalNumberOfReviews": 20,
                        "attribute": "appraisal",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 66.67
                    },
                    {
                        "clusterLabel": "Mixed opinions about the price",
                        "observationCount": 6,
                        "totalNumberOfObservations": 18,
                        "percentageOfObservationsVsTotalNumberOfReviews": 10,
                        "attribute": "appraisal",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 33.33
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Motivation to purchase toddler stools",
                        "observationCount": 33,
                        "totalNumberOfObservations": 58,
                        "percentageOfObservationsVsTotalNumberOfReviews": 55,
                        "attribute": "buyerMotivation",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 56.9
                    },
                    {
                        "clusterLabel": "To entertain kids and provide a fun play area",
                        "observationCount": 25,
                        "totalNumberOfObservations": 58,
                        "percentageOfObservationsVsTotalNumberOfReviews": 41.67,
                        "attribute": "buyerMotivation",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 43.1
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Sturdy and durable steps",
                        "observationCount": 33,
                        "totalNumberOfObservations": 58,
                        "percentageOfObservationsVsTotalNumberOfReviews": 55,
                        "attribute": "customerExpectations",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 56.9
                    },
                    {
                        "clusterLabel": "To provide a variety of engaging and educational play options",
                        "observationCount": 25,
                        "totalNumberOfObservations": 58,
                        "percentageOfObservationsVsTotalNumberOfReviews": 41.67,
                        "attribute": "customerExpectations",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 43.1
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Potential safety issue, sharp edges, flexible and crack, lack of information, unknown",
                        "observationCount": 6,
                        "totalNumberOfObservations": 14,
                        "percentageOfObservationsVsTotalNumberOfReviews": 10,
                        "attribute": "dangerAppraisal",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 42.86
                    },
                    {
                        "clusterLabel": "Safe for children, Safe for young children",
                        "observationCount": 8,
                        "totalNumberOfObservations": 14,
                        "percentageOfObservationsVsTotalNumberOfReviews": 13.33,
                        "attribute": "dangerAppraisal",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 57.14
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Attractive design, Simple design, Unknown",
                        "observationCount": 4,
                        "totalNumberOfObservations": 11,
                        "percentageOfObservationsVsTotalNumberOfReviews": 6.67,
                        "attribute": "designAndAppearance",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 36.36
                    },
                    {
                        "clusterLabel": "Cute and colorful design",
                        "observationCount": 7,
                        "totalNumberOfObservations": 11,
                        "percentageOfObservationsVsTotalNumberOfReviews": 11.67,
                        "attribute": "designAndAppearance",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 63.64
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Durability",
                        "observationCount": 21,
                        "totalNumberOfObservations": 24,
                        "percentageOfObservationsVsTotalNumberOfReviews": 35,
                        "attribute": "durability",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 87.5
                    },
                    {
                        "clusterLabel": "No information provided, Unknown",
                        "observationCount": 3,
                        "totalNumberOfObservations": 24,
                        "percentageOfObservationsVsTotalNumberOfReviews": 5,
                        "attribute": "durability",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 12.5
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Ease of Use",
                        "observationCount": 5,
                        "totalNumberOfObservations": 13,
                        "percentageOfObservationsVsTotalNumberOfReviews": 8.33,
                        "attribute": "easeOfUse",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 38.46
                    },
                    {
                        "clusterLabel": "Ease of use",
                        "observationCount": 8,
                        "totalNumberOfObservations": 13,
                        "percentageOfObservationsVsTotalNumberOfReviews": 13.33,
                        "attribute": "easeOfUse",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 61.54
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Used by kids for play",
                        "observationCount": 19,
                        "totalNumberOfObservations": 57,
                        "percentageOfObservationsVsTotalNumberOfReviews": 31.67,
                        "attribute": "howTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 33.33
                    },
                    {
                        "clusterLabel": "Used for various physical activities and games",
                        "observationCount": 38,
                        "totalNumberOfObservations": 57,
                        "percentageOfObservationsVsTotalNumberOfReviews": 63.33,
                        "attribute": "howTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 66.67
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Issues with product quality and durability",
                        "observationCount": 15,
                        "totalNumberOfObservations": 24,
                        "percentageOfObservationsVsTotalNumberOfReviews": 25,
                        "attribute": "issues",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 62.5
                    },
                    {
                        "clusterLabel": "No issues or complaints about the product",
                        "observationCount": 9,
                        "totalNumberOfObservations": 24,
                        "percentageOfObservationsVsTotalNumberOfReviews": 15,
                        "attribute": "issues",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 37.5
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "No information provided, Unknown",
                        "observationCount": 3,
                        "totalNumberOfObservations": 7,
                        "percentageOfObservationsVsTotalNumberOfReviews": 5,
                        "attribute": "noiseAndSmell",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 42.86
                    },
                    {
                        "clusterLabel": "No noise or smell",
                        "observationCount": 4,
                        "totalNumberOfObservations": 7,
                        "percentageOfObservationsVsTotalNumberOfReviews": 6.67,
                        "attribute": "noiseAndSmell",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 57.14
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Lack of packaging information and transparency",
                        "observationCount": 3,
                        "totalNumberOfObservations": 9,
                        "percentageOfObservationsVsTotalNumberOfReviews": 5,
                        "attribute": "packaging",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 33.33
                    },
                    {
                        "clusterLabel": "Packaging quality and materials",
                        "observationCount": 6,
                        "totalNumberOfObservations": 9,
                        "percentageOfObservationsVsTotalNumberOfReviews": 10,
                        "attribute": "packaging",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 66.67
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "All parts included and easy to assemble",
                        "observationCount": 4,
                        "totalNumberOfObservations": 10,
                        "percentageOfObservationsVsTotalNumberOfReviews": 6.67,
                        "attribute": "partsAndComponents",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 40
                    },
                    {
                        "clusterLabel": "Parts and components are incomplete or missing",
                        "observationCount": 6,
                        "totalNumberOfObservations": 10,
                        "percentageOfObservationsVsTotalNumberOfReviews": 10,
                        "attribute": "partsAndComponents",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 60
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Sturdy and durable materials with unknown quality",
                        "observationCount": 5,
                        "totalNumberOfObservations": 23,
                        "percentageOfObservationsVsTotalNumberOfReviews": 8.33,
                        "attribute": "quality",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 21.74
                    },
                    {
                        "clusterLabel": "Variations in quality perception",
                        "observationCount": 18,
                        "totalNumberOfObservations": 23,
                        "percentageOfObservationsVsTotalNumberOfReviews": 30,
                        "attribute": "quality",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 78.26
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Great toys for active play and learning",
                        "observationCount": 57,
                        "totalNumberOfObservations": 80,
                        "percentageOfObservationsVsTotalNumberOfReviews": 95,
                        "attribute": "reviewSummary",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 71.25
                    },
                    {
                        "clusterLabel": "Mixed reviews on product quality and functionality",
                        "observationCount": 23,
                        "totalNumberOfObservations": 80,
                        "percentageOfObservationsVsTotalNumberOfReviews": 38.33,
                        "attribute": "reviewSummary",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 28.75
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "All seasons, All year, Spring and summer",
                        "observationCount": 5,
                        "totalNumberOfObservations": 10,
                        "percentageOfObservationsVsTotalNumberOfReviews": 8.33,
                        "attribute": "season",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 50
                    },
                    {
                        "clusterLabel": "Seasonal events and weather conditions",
                        "observationCount": 5,
                        "totalNumberOfObservations": 10,
                        "percentageOfObservationsVsTotalNumberOfReviews": 8.33,
                        "attribute": "season",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 50
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "No information provided, Unknown",
                        "observationCount": 3,
                        "totalNumberOfObservations": 7,
                        "percentageOfObservationsVsTotalNumberOfReviews": 5,
                        "attribute": "setupAndInstructions",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 42.86
                    },
                    {
                        "clusterLabel": "No setup required, simple and clear instructions",
                        "observationCount": 4,
                        "totalNumberOfObservations": 7,
                        "percentageOfObservationsVsTotalNumberOfReviews": 6.67,
                        "attribute": "setupAndInstructions",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 57.14
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "No information provided, Unknown",
                        "observationCount": 3,
                        "totalNumberOfObservations": 12,
                        "percentageOfObservationsVsTotalNumberOfReviews": 5,
                        "attribute": "sizeAndFit",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 25
                    },
                    {
                        "clusterLabel": "Size and Fit",
                        "observationCount": 9,
                        "totalNumberOfObservations": 12,
                        "percentageOfObservationsVsTotalNumberOfReviews": 15,
                        "attribute": "sizeAndFit",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 75
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Children of various ages and abilities",
                        "observationCount": 49,
                        "totalNumberOfObservations": 61,
                        "percentageOfObservationsVsTotalNumberOfReviews": 81.67,
                        "attribute": "userDescription",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 80.33
                    },
                    {
                        "clusterLabel": "Kids, students, and children",
                        "observationCount": 12,
                        "totalNumberOfObservations": 61,
                        "percentageOfObservationsVsTotalNumberOfReviews": 20,
                        "attribute": "userDescription",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 19.67
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Various usage scenarios for the product",
                        "observationCount": 10,
                        "totalNumberOfObservations": 14,
                        "percentageOfObservationsVsTotalNumberOfReviews": 16.67,
                        "attribute": "whenTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 71.43
                    },
                    {
                        "clusterLabel": "When the product is used",
                        "observationCount": 4,
                        "totalNumberOfObservations": 14,
                        "percentageOfObservationsVsTotalNumberOfReviews": 6.67,
                        "attribute": "whenTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 28.57
                    }
                ]
            },
            {
                "clusters": [
                    {
                        "clusterLabel": "Indoor and outdoor play areas for children",
                        "observationCount": 28,
                        "totalNumberOfObservations": 54,
                        "percentageOfObservationsVsTotalNumberOfReviews": 46.67,
                        "attribute": "whereTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 51.85
                    },
                    {
                        "clusterLabel": "The product is used in various locations",
                        "observationCount": 26,
                        "totalNumberOfObservations": 54,
                        "percentageOfObservationsVsTotalNumberOfReviews": 43.33,
                        "attribute": "whereTheProductIsUsed",
                        "percentageOfObservationsVsTotalNumberPerAttribute": 48.15
                    }
                ]
            }
        ]
        // this.customerInsightsService.getCustomerInsights(id).subscribe(data => {
        //     console.log(JSON.stringify(data));
        // });
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
        ];
        this.negativeFeedbackData = [
            {
                "label": "Poor Sound Quality",
                "value": 31.2,
                "description": "Customers have reported mediocre sound quality, with some experiencing no sound at all. Others have reported poor sound quality in noisy environments, which can be frustrating and disruptive to their listening experience.",
                "count": 5673
            },
            {
                "label": "Poor Fit",
                "value": 22.0,
                "description": "Customers have reported that the earbuds do not stay in place and fall out easily, which can be frustrating and disruptive to their listening experience.",
                "count": 3995
            },
            {
                "label": "Earbuds Malfunction",
                "value": 18.1,
                "description": "Customers have reported issues with the earbuds falling off or falling out of their ears, which can be frustrating and disruptive to their listening experience.",
                "count": 3280
            },
            {
                "label": "Poor Durability",
                "value": 13.2,
                "description": "Customers have reported poor durability of the case, with some experiencing a broken or muffled sound in one earbud. Others have reported poor quality or a short lifespan, which can be frustrating and disappointing for users.",
                "count": 2402
            },
            {
                "label": "Connectivity Issues",
                "value": 12.2,
                "description": "Customers have reported poor connection quality, particularly when using the earbuds at the gym. Some have also experienced Bluetooth or pairing issues, which can be frustrating and disruptive to their listening experience.",
                "count": 2222
            },
            {
                "label": "Uneven Battery Life",
                "value": 12.0,
                "description": "Customers have reported poor sound quality compared to AirPods, as well as issues with the left earbud not holding a charge and a confusing battery indicator. This can be frustrating and inconvenient for users.",
                "count": 2174
            },
            {
                "label": "Lack Of Noise Cancellation",
                "value": 8.0,
                "description": "Customers have reported poor noise cancellation, with some describing it as inconsistent or ineffective. This can be frustrating for users who are looking for a more immersive listening experience.",
                "count": 1445
            },
            {
                "label": "Charging Issues",
                "value": 6.5,
                "description": "Customers have reported issues with the charging case, including one earbud failing to charge or the left earbud not charging at all. This can be frustrating and inconvenient for users.",
                "count": 1176
            },
            {
                "label": "Difficult To Use",
                "value": 6.3,
                "description": "Customers have reported difficulty with touch commands and controls, as well as difficulty removing the earbuds from the case. This can be frustrating and time-consuming for users.",
                "count": 1145
            },
            {
                "label": "Lacks Volume Control",
                "value": 6.2,
                "description": "Customers have reported low volume, with some describing the earbuds as not loud enough. However, others have reported that the earbuds can be very loud, which can be frustrating for users who are looking for more control over their listening experience.",
                "count": 1133
            }
        ];
        this.buyersMotivationData = [
            {
                "label": "Good Value For Price",
                "value": 67.0,
                "description": "Customers have found these earbuds to be a great value for the price, staying in ears well and providing impressive sound for the price. Some have also noted good customer service.",
                "count": 5707
            },
            {
                "label": "Great Sound Quality",
                "value": 12.0,
                "description": "Customers have found these earbuds to be fantastic, with great sound quality and staying connected to Bluetooth for music and calls.",
                "count": 1023
            },
            {
                "label": "Positive Recommendation",
                "value": 4.6,
                "description": "Customers have left positive reviews and recommendations for the headphones, citing good audio quality and value for money. Some customers have also purchased the headphones as a gift for loved ones, such as husbands.",
                "count": 389
            },
            {
                "label": "Comfortable Fit",
                "value": 3.5,
                "description": "Customers have found these earbuds to be comfortable for long wear, extremely comfortable, and good for small ears.",
                "count": 298
            },
            {
                "label": "Durable And High Quality",
                "value": 3.2,
                "description": "Customers have noted the build quality and good quality feel for the case, making these earbuds durable and high quality.",
                "count": 271
            },
            {
                "label": "Amazing Battery Life",
                "value": 2.9,
                "description": "Customers have noted that these earbuds have auto-pairing, outstanding battery life, and are highly recommended.",
                "count": 245
            },
            {
                "label": "Wireless Connectivity",
                "value": 2.8,
                "description": "Customers have praised the headphones for their wireless connectivity, including wireless charging and long battery life.",
                "count": 242
            },
            {
                "label": "Recommended By Others",
                "value": 2.7,
                "description": "Customers have been recommended the headphones by others, either for stationary use or due to the brand name.",
                "count": 229
            },
            {
                "label": "Noise Cancelling",
                "value": 1.8,
                "description": "Customers have noted that these earbuds have active noise cancellation, better noise cancellation and battery life than Airpods, and fantastic quality for phone talk.",
                "count": 156
            },
            {
                "label": "Easy To Use",
                "value": 1.8,
                "description": "Customers have found these earbuds to be inexpensive and easy to use, great for casual use and easy pairing.",
                "count": 154
            }
        ];
        this.customerExpectationsData = [
            {
              "label": "Better Sound Quality",
              "value": 15.5,
              "description": "Customers appreciate the improved sound quality of the headphones, including less choppy sound and adjustable earbuds.",
              "count": 499
            },
            {
              "label": "Better Design",
              "value": 12.8,
              "description": "Customers appreciate the better packaging and less slippery case, as well as hard buttons for easier control.",
              "count": 412
            },
            {
              "label": "Higher Quality Product",
              "value": 12.0,
              "description": "Customers appreciate the higher quality materials and better call quality of the headphones compared to other products.",
              "count": 385
            },
            {
              "label": "Improved Battery Life",
              "value": 11.6,
              "description": "Customers appreciate the improved charging case and reliable battery indicator of the headphones.",
              "count": 373
            },
            {
              "label": "Better Fit",
              "value": 10.8,
              "description": "Customers appreciate the secure fit and stable volume control of the headphones, as well as their ability to stay in the ears during use.",
              "count": 348
            },
            {
              "label": "Longer Lifespan",
              "value": 9.5,
              "description": "Customers have reported that these earbuds have a longer lifespan than other brands they have tried, with some lasting for years without any issues. The durability of the earbuds has also been praised, with many users stating that they have survived accidental drops and daily wear and tear.",
              "count": 304
            },
            {
              "label": "Better Durability",
              "value": 6.2,
              "description": "Customers appreciate the improved durability and quality of the headphones, including a more protective case.",
              "count": 198
            },
            {
              "label": "Better Noise Cancellation",
              "value": 4.5,
              "description": "Customers appreciate the improved noise cancellation and audio quality of the headphones, including less static noise and interference when moving.",
              "count": 144
            },
            {
              "label": "Working Product",
              "value": 4.3,
              "description": "Customers have reported that these earbuds work well and provide a functional charging experience. The battery life has been praised, with some users reporting that they can use the earbuds for several hours without needing to recharge.",
              "count": 139
            },
            {
              "label": "Louder Volume",
              "value": 3.4,
              "description": "Users have found that these earbuds can reach higher volume levels without any glitches or distortion, allowing them to enjoy their music at a louder volume. The overall sound quality has also been praised, with many users stating that they can hear more detail in their music.",
              "count": 109
            }
        ];
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
